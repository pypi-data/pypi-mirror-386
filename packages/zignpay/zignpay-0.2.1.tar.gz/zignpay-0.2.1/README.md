# ZIGNPAY

[![build-status-image]][build-status]
[![coverage-status-image]][codecov]
[![pypi-version]][pypi]

## Make mobile payment easy

## Overview

A package to manage mobile payments using the MTN MoMo and Orange Money APIs

Some reasons you might want to use REST framework:

* Add a payment method to your website or application
* Create a mobile payment app
* Customization and extensibility
* Support for multiple operators

## Steps summary

* Sign up for an account
* Get a product subscription key
* Installation
* Create an API user and API key
* Initialize the collection class
* Make a payment request

## Getting Started

__Sign up for an account__

Head over to [https://momodeveloper.mtn.com/](https://momodeveloper.mtn.com/) and create your account. Once created, verify your account and sign in to the developer dashboard.

__Get a product subscription key__

The momo developer API is segmented into different products. Like; Collections, Remittances, Disbursement, and a collections widget. [Find and Subscribe](https://momodeveloper.mtn.com/products) to the product that your application will be using. For the case of this tutorial, we shall subscribe to the collections product. It enables us to make a remote collection of fees and bills. Once subscribed, you shall be able to get a _primary subscription key_ and a _secondary subscription key_ in your [developer dashboard](https://momodeveloper.mtn.com/developer).

__Installation__

## Requirements

* Python 3.10+

```bash
  pip install zignpay
```

__Create an API user__

```python
  import os
  from zignpay.momo import MomoApiProvisioning, MomoCollection


  """
    Here we will subscribe to the product collection.
  """  
  subscription_key = os.environ('subscription_key') # Put the subscription key that you copied

  """
    Keep in mind that your subscription key in development is different in production,
    To go into production you must click on Go Live in your Dashboard
  """
```

The MOMO API relies heavily on unique identifying identifiers called UUIDs. Each API user you create will have a unique UUID, zignpay will generate this automatically for you.

```python
  ...
  momo = MomoApiProvisioning({
    "subscription_key" : subscription_key, 
    "environment" : "DEV" # Define DEV if you are in development and PROD if you are in production
  })

  api_user = momo.create_api_user() # This returns the unique reference (UUID) of the created API user

  if api_user: #Check if the query returns an object
    api_key = momo.create_api_key() # Then generate the API key
    """
      You can save these two values ​​in a secure database, they will be necessary later.
    """
```

__Initialize the collection class__

```python
  ...
  collection = MomoCollection({
    "api_user_id" : api_user, # The user reference created above
    "api_key" : api_key, # The api key created above
    "subscription_key" : subscription_key, # The subscription key for the collection product
    "environment" : "DEV",
    "country_code" : "CM", # our Country Codes Alpha-2
  })
```

You will find your [Country codes](https://www.iban.com/country-codes) here.

__Make a payment request__

```python
  ...
  requestToPay = collection.request_to_pay({
    "amount": 15, # Payment request amount
    "from": "2376xxxxxxxx", # Example of Cameroonian number
    "reference_id": "123456789", 
    "description": "Requested to pay" # Put your own description
  })
```

Example query result

```python
  {
    'financialTransactionId': '490639485', 
    'externalId': '123456789', 
    'amount': '15', 
    'currency': 'EUR', 
    'payer': {
      'partyIdType': 'MSISDN', 
      'partyId': '2376xxxxxxxx'
      }, 
    'payerMessage': 'Requested to pay', 
    'payeeNote': 'Thank you for your payment', 
    'status': 'SUCCESSFUL'
  }
```

__We are currently working on improving this documentation__
