# AWS Step Functions: Handling Contextual Messages in Serverless Architectures

See full article here: [https://blog.devops.dev/handling-contextual-messages-in-serverless-architectures-ecbf3ef731b1](https://blog.devops.dev/handling-contextual-messages-in-serverless-architectures-ecbf3ef731b1)

In modern serverless applications—particularly those interacting with messaging platforms like Telegram,  WhatsApp—messages, Instagram, and other often arrive individually, without any native session or context. While this fits well with AWS Lambda's stateless execution model, it introduces a fundamental challenge: how to maintain context across messages.

For instance, a user might send multiple sequential messages that together represent a single intent or session. Without orchestration, each message might trigger its own Lambda execution, causing the system to respond prematurely or without full context.

This tutorial presents a clean, serverless solution to manage such contextual flows.

## Goal of This Tutorial

We will simulate an architecture where messages from a user are collected over time and processed only after a period of inactivity (e.g., 30 seconds). This model is especially effective when building chatbots, customer service interfaces, or event-driven backends that need to handle multi-message sessions.

Key technologies used:
- AWS Lambda
- AWS Step Functions
- Amazon DynamoDB

To keep it straightforward:
- We’ll trigger the flow manually using the AWS Console (i.e., no direct integration with an external messaging API).
- We'll use two DynamoDB tables:
  - `UserMessageBufferTable`: temporarily stores user messages during an active session.
  - `ConsolidatedMessagesTable`: stores the finalized, grouped session data.

--- 

## Architecture Overview

### Message Lifecycle and Flow

1. A user message arrives and invokes the `StepFunctionLauncher` Lambda.
2. The Lambda stores the message in the `UserMessageBufferTable` DynamoDB table.
3. It checks whether a Step Function execution is already running for the `user_id`.
4. If no execution exists, it starts a new execution of the Step Function (`ConversationAggregator`).
5. The Step Function wait 30 seconds and invokes the `CheckMessageFreshnessLambda`.
6. The `CheckMessageFreshnessLambda` reads messages from the `UserMessageBufferTable` table and checks if the most recent message is older than 30 seconds.
7. If inactivity is confirmed, the Step Function proceeds to invoke the `MessageConsolidatorLambda`.
8. If inactivity is not confirmed, the Step Function calculate a remaining wait time and Step Function wait this time.
9. The `MessageConsolidatorLambda` consolidates all user messages, stores the result in the `ConsolidatedMessagesTable` DynamoDB table, and deletes the original entries from the `UserMessageBufferTable`.

---

### Architecture Diagram

![Architecture](img/stepfunction_architecture.jpg)

**Description of Architecture Diagram Steps**

1. A new user message is received and triggers the `StepFunctionLauncherLambda` Lambda function.
2. The Lambda stores the message in the `UserMessageBufferTable` DynamoDB table.
3. The Lambda initiates a Step Function (`ConversationAggregator`) if no active execution exists for the `user_id`.
4. The Step Function invokes the `CheckMessageFreshnessLambda` to assess message activity.
5. The `CheckMessageFreshnessLambda` reads messages from `UserMessageBufferTable` and determines if the user has been inactive for a defined period (e.g., 30 seconds).
6. Once inactivity is confirmed, the Step Function proceeds to invoke the `MessageConsolidatorLambda`.
7. The `MessageConsolidatorLambda` consolidates buffered messages and writes the result to the `ConsolidatedMessagesTable` DynamoDB table.


---

## Step-by-Step Guide 

### Step 1: Create the `UserMessageBufferTable` Table

In the AWS Console:
1. Navigate to **DynamoDB > Tables**.
2. Click **Create table**.
3. Set `Table name` to `UserMessageBufferTable`.
4. Set the **Partition key** to `user_id` (String).
5. Set the **Sort key** to `timestamp` (String).
6. Choose **On-demand (Pay-per-request)** capacity mode.
7. Optionally, add a **GSI** named `gsi_session_id` with `session_id` as the partition key.
8. Click **Create table**.

Alternatively, you can create it using the code from `DynamoDbCreateBuffer.py`

--- 

### Step 2: Create the `ConsolidatedMessagesTable` Table

In the AWS Console:
1. Navigate to **DynamoDB > Tables**.
2. Click **Create table**.
3. Set `Table name` to `ConsolidatedMessagesTable`.
4. Set the **Partition key** to `user_id` (String).
5. Set the **Sort key** to `session_end_timestamp` (String).
6. Choose **On-demand (Pay-per-request)** capacity mode.
7. Optionally, add a **GSI** named `gsi_channel` with `channel` as the partition key.
8. Click **Create table**.

You may also use the code code from `DynamoDbCreateConsolidate.py`

--- 

### Step 3: Create the `CheckMessageFreshnessLambda` Function

In the AWS Console:
1. Go to **Lambda > Create function**.
2. Choose **Author from scratch**.
3. Set the function name to `CheckMessageFreshnessLambda`.
4. Choose Python as the runtime (e.g., Python 3.13).
5. Click **Create function**.
6. In the function code editor, replace the default handler with code presented bellow.
7. Deploy the function.


---

### Step 4: Create the `MessageConsolidatorLambda` Function

Repeat the same steps as in Step 3 with the following differences:
- Function name: `MessageConsolidatorLambda`
- Runtime: Python (same as above)
- Use this handler code:


--- 

### Step 5: Create the Step Function (State Machine)

In the AWS Console:
1. Navigate to **Step Functions > State machines**.
2. Click **Create state machine**.
3. Choose **Author with code snippets**.
4. Name the state machine `ConversationAggregator`.
5. Select **Standard** type.
6. Paste the state machine definition in the editor (code bellow)
7. For each Lambda used (`CheckMessageFreshnessLambda` and `MessageConsolidatorLambda`), ensure correct IAM permissions and function ARNs are applied.
8. Click **Next**, configure permissions, then **Create state machine**.

--- 

### Step 6: Create the `StepFunctionLauncherLambda` Function

In the AWS Console:
1. Go to **Lambda > Create function**.
2. Name the function `StepFunctionLauncherLambda`.
3. Choose Python as the runtime.
4. Paste the following code in the handler (code bellow).
5. Ensure this Lambda has permissions to: (i) Write to the `UserMessageBufferTable` table. (ii) Start executions in Step Functions.
6. Deploy the function.

--- 

### Step 7: Testing the Integration

To simulate messages:
1. In the AWS Console, go to the **StepFunctionLauncherLambda** function.
2. Click **Test** and create a new test event.
3. Use the following sample payloads presented bellow.
4. Trigger the test multiple times within 30 seconds to simulate an active session.
5. Observe how Step Functions waits before consolidation.
6. Check the `ConsolidatedMessagesTable` table for grouped session data.

**User 1 Test Payload:**

```json
{
  "user_id": "user-001",
  "message": {
    "text": "Hi, I need support.",
    "type": "text",
    "channel": "telegram"
  }
}
```

**User 2 Test Payload:**
```json
{
  "user_id": "user-002",
  "message": {
    "text": "Can you help me with billing?",
    "type": "text",
    "channel": "whatsapp"
  }
}
```

---

## Conclusion

By following this guide, you’ve implemented a fully serverless solution for handling contextual message flows using AWS Step Functions, Lambda, and DynamoDB. The architecture is scalable, event-driven, and well-suited for building intelligent, session-aware chat interfaces and automation workflows.

---

## Stay Connected

If you found this guide helpful, stay connected for more insights on **AI, cloud security, and AWS automation**:
- **LinkedIn:** [https://www.linkedin.com/in/biagolini](https://www.linkedin.com/in/biagolini)
- **Medium:** [https://medium.com/@biagolini](https://medium.com/@biagolini)
- **GitHub:** [https://github.com/biagolini](https://github.com/biagolini)

Happy building with **AWS!** 🚀
