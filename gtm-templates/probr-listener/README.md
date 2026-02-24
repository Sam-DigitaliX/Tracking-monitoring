# Probr — Server-Side Listener Tag

A Google Tag Manager **server-side** tag template that monitors all events and tag executions flowing through your sGTM container, sending real-time data to your [Probr](https://probr.io) dashboard.

Works with **any sGTM hosting provider**: Stape, Addingwell, self-hosted (GCP, AWS), or any other setup.

## What it monitors

| Metric | Description |
|---|---|
| **Tag health** | Success/failure/timeout/exception status for every tag that fires |
| **Execution time** | How long each tag takes to execute (ms) |
| **Event volumes** | Count of each event type (page_view, purchase, add_to_cart, etc.) |
| **User data quality** | Presence of enhanced conversion fields: email, phone, address |
| **E-commerce quality** | Presence of value, currency, transaction_id, items on conversion events |

## Setup

### 1. Get your Probr Ingest Key

In the Probr dashboard, go to **Sites** > select your site > copy the **Ingest Key**.

### 2. Add the tag to your server container

1. In your GTM **server** container, go to **Templates** > **Tag Templates** > **Search Gallery**
2. Search for **Probr** and add the **Probr — Server-Side Listener** template
3. Create a new tag using this template
4. Configure:
   - **Probr Ingest Endpoint**: `https://your-probr-instance.com/api/ingest`
   - **Probr Ingest Key**: paste the key from step 1
   - **Track user data quality**: enable to monitor enhanced conversions data
   - **Send mode**: `Per event` (recommended) or `Batched`

### 3. Set the trigger

Set the trigger to **All Events** (or a custom trigger if you want to limit monitoring to specific events).

### 4. Add tag metadata (recommended)

For the tag to report **tag names** (not just IDs) in the Probr dashboard:

1. For each tag you want to monitor, go to tag settings
2. Under **Additional Tag Metadata**, add a key-value pair: key = `name`, value = the tag's display name

### 5. Publish

Publish a new version of your server container. Data will start flowing to your Probr dashboard within seconds.

## Send modes

| Mode | Behavior | Best for |
|---|---|---|
| **Per event** | One HTTP POST per event to the Probr API | Most reliable, real-time monitoring |
| **Batched** | Buffers N events in memory, sends one aggregated POST | Lower network overhead, high-traffic sites |

> **Note**: In batched mode, data is stored in `templateDataStorage` which is per-instance. If your sGTM setup uses multiple Cloud Run instances, each instance maintains its own buffer. Data may be lost if an instance is terminated before the buffer flushes.

## Tag exclusion

To prevent the Probr tag from monitoring itself (creating a feedback loop), add its tag ID to the **Tag IDs to Exclude** field. You can find the tag ID in GTM under the tag's settings.

## Data flow

```
Browser → sGTM Container → Tags fire → addEventCallback
                                              ↓
                                    Probr Listener Tag
                                              ↓
                                   POST /api/ingest
                                              ↓
                                    Probr Backend
                                    (aggregation)
                                              ↓
                                   Probr Dashboard
                              (tag health, volumes,
                               user data quality)
```

## Permissions

This tag requires the following server-side permissions:

| Permission | Reason |
|---|---|
| `send_http` | Send monitoring data to the Probr API |
| `read_event_data` | Read event name, user_data, and e-commerce parameters |
| `access_template_storage` | Buffer events in batched mode |
| `read_container_data` | Read the container ID |
| `logging` | Debug logging in GTM preview mode |

## License

Apache License 2.0 — see [LICENSE](./LICENSE).
