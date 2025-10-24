===========
Mercury SDK
===========

Mercury SDK can be used in projects that interface with the mercury service
that provides common internal functionality.

Initializing the client
-------------------------------
::

  from mercuryclient import MercuryApi
  # Setup connection parameters
  conn_params = {'username': 'mercury_username', 'password':'password', 'url':'https://mercury-url.com'}
  m = MercuryApi(conn_params)
  m.send_mail(['recipent@email.com'],'Test mail', 'Mail body','ses','ses_profile')

Available APIs:
----------------------
- send_mail
- send_sms
- request_experian_report
- get_experian_response
- fetch_experian_report
- request_cibil_report
- get_cibil_response
- fetch_cibil_report
- request_highmark_report
- get_highmark_response
- fetch_highmark_report
- request_verify_id
- get_verify_id_result
- request_bank_statement
- get_bank_statement_result
- verify_webhook
- insurance
- secure_patyment_recharge
   - get_operators_list
   - make_recharge
   - get_recharge_status
   - get_recharge_wallet_balance
   - get_recharge_ip
   - get_recharge_plans
- bbps
   - set_agent_on_board
   - get_state
   - get_district_by_state
   - get_bill_categories
   - get_biller_by_categories
   - get_customer_params_by_biller_id
   - get_amount
   - send_bill_payment_request_transid
   - send_bill_payment_request
   - get_duplicate_payment_receipt
   - register_trasaction_complaint
   - register_service_complaint
   - get_complaint_status
   - get_bbpsid
- verify_bank_account
- verify_gstin
- get_verify_gst_result
- generate_okyc_otp
- verify_okyc_otp
- fetch_rc_details
- verify_udyog_aadhaar
- fetch_equifax_report
- generate_liveness_session_id
- get_liveness_session_result
- extract_itr_details
- fetch_itr_report
- generate_epfo_otp
- verify_epfo_otp
- get_epfo_details
- name_match
- check_e_sign
- create_indv_entity
- create_legal_entity
- payments 
    - generate_qr_code
    - close_qr_code
    - generate_payment_plan
    - create_payment_subscription
    - fetch_subscription
    - generate_payment_link
    - cancel_payment_link
    - charge_subscription
    - manage_subscription
    - emandate_registration
    - emandate_payment_token
    - emandate_order
    - emandate_recurring_payments

Types:
------
For complex requests like CIBIL, Experian or Highmark, you can construct the request
JSON using the provided pydantic models. The types are available at *mercury.types.<request_type>.request*.

Example using models for generating Highmark Request::

  from mercuryclient.types.highmark.request import Applicant, HighmarkRequest
  applicant = Applicant(name="Example Name" ...)
  request_obj = HighmarkRequest(
      applicant=applicant,
      inquiry_reference_number="ABCDE",
      ...
  )
  # After generating your request, pass the object to the corresponding request
  m.fetch_highmark_report(request_obj, profile="sample_profile)

Testing:
-------------
Tests are run under *tox*

You can install tox with

>>> pip install tox

If using pyenv - you can do the following steps before running tox
(patch version will depend on your installations - tox only considers the major version)

>>> pyenv local 3.7.3 3.6.8 3.8.1

Without this step - tox will not be able to find the interpreters

Run tests using the following command

>>> tox
