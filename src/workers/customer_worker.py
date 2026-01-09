"""
Customer creation worker for QuickBooks Desktop Test Tool.

Background worker for creating customers, jobs, and sub-jobs in QuickBooks.
"""

import json
from tkinter import messagebox
from qb import QBIPCClient, disconnect_qb
from qb.qbfc_connection import QBFCConnectionError
from mock_generation import CustomerGenerator
from store import add_customer
from app_logging import LOG_NORMAL, LOG_VERBOSE, LOG_DEBUG
from app_logging.logging_config import should_log
from config import AppConfig


def _format_customer_debug(customer_data: dict, result: dict) -> tuple:
    """Format customer operation debug info for logging."""
    # Request info: show ALL data being sent
    request_str = json.dumps(customer_data, indent=2, default=str)

    # Response info
    if result.get('success'):
        data = result.get('data', {})
        response_str = f"list_id={data.get('list_id')}, full_name={data.get('full_name')}"
    else:
        response_str = f"ERROR: {result.get('error', 'Unknown error')}"

    return request_str, response_str


def create_customer_worker(app, email: str, field_config: dict, manual_values: dict,
                           num_jobs: int = 0, num_subjobs: int = 0):
    """
    Worker function to create customer and jobs in background.

    Args:
        app: Reference to the main application instance
        email: Customer email address
        field_config: Configuration for random vs manual fields
        manual_values: Manual field values when not using random
        num_jobs: Number of jobs to create under the customer
        num_subjobs: Number of sub-jobs to create under each job
    """
    try:
        # Step 1: Create the parent customer
        app.root.after(0, lambda: app._log_create(f"Generating customer data with email: {email}"))

        customer_data = CustomerGenerator.generate_customer(
            email=email,
            field_config=field_config,
            manual_values=manual_values
        )

        app.root.after(0, lambda: app._log_create(f"Creating customer: {customer_data['name']}"))

        # Send to QuickBooks via QBFC
        qb = QBIPCClient()
        parser_result = qb.execute_operation('add_customer', {'customer_data': customer_data})

        # DEBUG: Log request and response (only if DEBUG is enabled)
        if should_log(LOG_DEBUG, AppConfig.get_log_level()):
            req_str, resp_str = _format_customer_debug(customer_data, parser_result)
            app.root.after(0, lambda n=customer_data['name'], r=req_str:
                          app._log_create(f"  [DEBUG {n}] Request: {r}", LOG_DEBUG))
            app.root.after(0, lambda n=customer_data['name'], r=resp_str:
                          app._log_create(f"  [DEBUG {n}] Response: {r}", LOG_DEBUG))

        if not parser_result['success']:
            error_msg = parser_result.get('error', 'Unknown error')
            app.root.after(0, lambda: app._log_create(f"✗ Customer creation failed: {error_msg}"))
            app.root.after(0, lambda: messagebox.showerror("Error", error_msg))
            return

        # Customer created successfully
        customer_info = parser_result['data']
        customer_list_id = customer_info['list_id']
        customer_data['list_id'] = customer_list_id
        customer_data['full_name'] = customer_info['full_name']
        customer_data['created_by_app'] = True
        app.store.dispatch(add_customer(customer_data))

        app.root.after(0, lambda: app._log_create(f"✓ Customer created: {customer_info['full_name']}"))
        app.root.after(0, app._update_customer_combo)

        # Step 2: Create jobs if requested
        if num_jobs > 0:
            app.root.after(0, lambda: app._log_create(f"Creating {num_jobs} job(s)...", LOG_VERBOSE))

            for job_idx in range(num_jobs):
                try:
                    # Generate job data
                    job_data = CustomerGenerator.generate_job(
                        parent_customer_ref=customer_list_id,
                        email=email,
                        is_subjob=False
                    )

                    job_num = job_idx + 1
                    app.root.after(0, lambda n=job_num, total=num_jobs, name=job_data['name']:
                                  app._log_create(f"  Creating job {n}/{total}: {name}", LOG_VERBOSE))

                    # Send to QuickBooks via QBFC
                    parser_result = qb.execute_operation('add_customer', {'customer_data': job_data})

                    # DEBUG: Log request and response (only if DEBUG is enabled)
                    if should_log(LOG_DEBUG, AppConfig.get_log_level()):
                        req_str, resp_str = _format_customer_debug(job_data, parser_result)
                        app.root.after(0, lambda jn=job_num, r=req_str:
                                      app._log_create(f"  [DEBUG Job {jn}] Request: {r}", LOG_DEBUG))
                        app.root.after(0, lambda jn=job_num, r=resp_str:
                                      app._log_create(f"  [DEBUG Job {jn}] Response: {r}", LOG_DEBUG))

                    if not parser_result['success']:
                        error_msg = parser_result.get('error', 'Unknown error')
                        app.root.after(0, lambda n=job_num, err=error_msg:
                                      app._log_create(f"  ✗ Job {n} failed: {err}"))
                        continue

                    # Job created successfully
                    job_info = parser_result['data']
                    job_list_id = job_info['list_id']
                    # Add job to store
                    job_data['list_id'] = job_list_id
                    job_data['full_name'] = job_info['full_name']
                    job_data['sublevel'] = 1
                    job_data['created_by_app'] = True
                    app.store.dispatch(add_customer(job_data))
                    app.root.after(0, lambda n=job_num, name=job_info['full_name']:
                                  app._log_create(f"  ✓ Job {n}/{num_jobs} created: {name}", LOG_VERBOSE))

                    # Step 3: Create sub-jobs for this job if requested
                    if num_subjobs > 0:
                        for subjob_idx in range(num_subjobs):
                            try:
                                # Generate sub-job data
                                subjob_data = CustomerGenerator.generate_job(
                                    parent_customer_ref=job_list_id,
                                    email=email,
                                    is_subjob=True
                                )

                                subjob_num = subjob_idx + 1
                                app.root.after(0, lambda jn=job_num, sn=subjob_num, total=num_subjobs, name=subjob_data['name']:
                                              app._log_create(f"    Creating sub-job {sn}/{total} for job {jn}: {name}", LOG_VERBOSE))

                                # Send to QuickBooks via QBFC
                                parser_result = qb.execute_operation('add_customer', {'customer_data': subjob_data})

                                # DEBUG: Log request and response (only if DEBUG is enabled)
                                if should_log(LOG_DEBUG, AppConfig.get_log_level()):
                                    req_str, resp_str = _format_customer_debug(subjob_data, parser_result)
                                    app.root.after(0, lambda jn=job_num, sn=subjob_num, r=req_str:
                                                  app._log_create(f"  [DEBUG SubJob {jn}.{sn}] Request: {r}", LOG_DEBUG))
                                    app.root.after(0, lambda jn=job_num, sn=subjob_num, r=resp_str:
                                                  app._log_create(f"  [DEBUG SubJob {jn}.{sn}] Response: {r}", LOG_DEBUG))

                                if not parser_result['success']:
                                    error_msg = parser_result.get('error', 'Unknown error')
                                    app.root.after(0, lambda sn=subjob_num, err=error_msg:
                                                  app._log_create(f"    ✗ Sub-job {sn} failed: {err}"))
                                    continue

                                # Sub-job created successfully
                                subjob_info = parser_result['data']
                                # Add subjob to store
                                subjob_data['list_id'] = subjob_info['list_id']
                                subjob_data['full_name'] = subjob_info['full_name']
                                subjob_data['sublevel'] = 2
                                subjob_data['created_by_app'] = True
                                app.store.dispatch(add_customer(subjob_data))
                                app.root.after(0, lambda sn=subjob_num, name=subjob_info['full_name']:
                                              app._log_create(f"    ✓ Sub-job {sn}/{num_subjobs} created: {name}", LOG_VERBOSE))

                            except Exception as e:
                                error_str = str(e)
                                app.root.after(0, lambda sn=subjob_idx+1, err=error_str:
                                              app._log_create(f"    ✗ Sub-job {sn} error: {err}"))

                except Exception as e:
                    error_str = str(e)
                    app.root.after(0, lambda n=job_idx+1, err=error_str:
                                  app._log_create(f"  ✗ Job {n} error: {err}"))

            # Summary and update combo with all new jobs/subjobs
            total_created = 1 + num_jobs + (num_jobs * num_subjobs)
            app.root.after(0, app._update_customer_combo)
            app.root.after(0, lambda t=total_created:
                          app._log_create(f"✓ All done! Created {t} total record(s)"))
        else:
            app.root.after(0, lambda: app._log_create(f"✓ Customer creation complete!"))

    except QBConnectionError as e:
        error_str = str(e)
        app.root.after(0, lambda: app._log_create(f"✗ QB Connection Error: {error_str}"))
        app.root.after(0, lambda: messagebox.showerror("QB Connection Error", error_str))
    except Exception as e:
        error_str = str(e)
        app.root.after(0, lambda: app._log_create(f"✗ Unexpected Error: {error_str}"))
        app.root.after(0, lambda: messagebox.showerror("Error", error_str))
    finally:
        # Disconnect from QuickBooks after batch operation completes
        disconnect_qb()
        # Auto-save session after creating customers
        app.root.after(0, lambda: app._auto_save_session())
        # Re-enable button and update status (handle both Testing and Accounting modes)
        def reenable_button():
            if hasattr(app, 'create_customer_btn') and app.create_customer_btn:
                app.create_customer_btn.config(state='normal')
            if hasattr(app, 'acct_create_btn') and app.acct_create_btn:
                app.acct_create_btn.config(state='normal')
        app.root.after(0, reenable_button)
        app.root.after(0, lambda: app.status_bar.config(text="Ready"))
