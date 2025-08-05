28 July 

Use case preparation 
Scenario: 
A user is performing packing at a designated packing bench. 
 
📦 Packing Workflow 
1. Packing Action 
• The user completes packing and clicks the “Pack” button on the Pack screen. 
2. API Call to Carrier Management System (CMS) 
• This triggers an API request to the CMS to generate a shipping label or confirm carrier allocation. 
3. API Response Handling 
• If the API response is successful, the process continues normally. 
• If the API response is a failure, the user raises an IT support ticket for assistance. 
 
🛠️ IT Team Investigation 
 
Upon receiving the ticket, the IT team: 
• Looks up CMS logs based on the order ID or container ID reported. 
• Identifies the cause of the API failure. 
 
❌ Common Failure Scenarios and Resolutions 
 
Error Type Description IT Team Resolution 
Invalid Postcode CMS rejects the request due to a wrong or unrecognized postcode. Ask the user to verify and correct the postcode in the system. 
Null Payload CMS returns no data in the response (payload is empty or missing). Instruct the user to repack the container and reattempt. 
Hazmat Issue One or more items have hazmat flags triggering CMS restrictions. Ask the user to verify SKUs for correct hazmat ID and class. 
 
 
Use Case: AI-Powered ITSM Analyst for Carrier API Failure Support 
 
⚙️ AI-Integrated Workflow Overview 
 
✅ Step 1: Packing and API Call 
• The user packs the order and clicks “Pack”. 
• The system automatically sends an API request to CMS. 
• The API may return a: 
• Success – process continues. 
• Failure – AI ITSM Analyst is triggered. 
 
 
🤖 Step 2: AI-Powered Incident Detection & Triage 
 
If the CMS API response is a failure, the AI ITSM Analyst (LLM-powered) steps in: 
1. Intercepts the error response (through user report). 
2. Parses the error logs and identifies the root cause using: 
• Order ID 
• Container ID 
• Error message from CMS 
3. Matches the issue with known error patterns in its knowledge base. 
 
💡 Step 3: AI Response and Guidance 
 
Based on the issue detected, the AI provides automated resolution guidance to the warehouse associate: 
 
CMS Error Detected AI-Powered Response 
Invalid Postcode “The postcode seems invalid. Please verify and correct it before retrying.” 
Null Payload “The CMS response is empty. Please repack the container and try again.” 
Hazmat Issue “This may be due to hazardous materials. Please check the SKU’s hazmat ID and classification.” 
 
• If the issue is resolved after user action, the AI closes the incident. 
• If the issue persists or is unknown, the AI automatically escalates to the human IT team. 
 
📧 Step 4: Automatic Ticket Creation & Escalation 
 
For unknown or unresolved issues: 
• AI raises a support ticket and logs all relevant details: 
• Order ID 
• Container ID 
• Timestamp 
• CMS error response 
• Steps already performed 
• Sends a summary email or alert to the IT team for manual intervention. 
 
 
Sample Prompts 
🔁 Sample Conversation 1: Invalid Postcode 
 
🧑 User: 
I tried to pack order ORD34251, but I got an error. 
 
🤖 AI Analyst: 
Got it. Let me check the CMS response for order ORD34251… 
The API returned a failure due to an invalid postcode. 
 
✅ Please verify and correct the postcode in the system, then try packing again. 
 
🧑 User: 
Okay, I corrected the postcode and tried again. It worked. 
 
🤖 AI Analyst: 
Great! Packing was successful. 
I’m closing this incident. Let me know if you need help with anything else. 
 
 
🔁 Sample Conversation 4: Unknown Issue (Escalation) 
 
🧑 User: 
 
Order ORD5001 is failing, and I don’t know why. 
 
🤖 AI Analyst: 
Checking CMS response logs… 
❌ The issue doesn’t match any known error patterns. 
 
I’ve logged this as a new incident and notified the IT team. 
📝 Incident ID: INC-5012 
 
Time Saved Per Incident 
  •  Manual effort (IT triage): 20–30 mins 
  •  AI agent handling time: ~1–2 mins 
  •  Time saved per known issue: ~18–28 minutes 
 
Summary  
Goal 
 
To build an AI-powered ITSM Analyst that assists warehouse users when a carrier API fails during packing, using an LLM to detect known issues, provide real-time guidance, and escalate unresolved incidents — reducing IT team workload and improving resolution time. 
 
LLM Role in the System 
• Error Triage & Classification: Parses API error responses tied to order ID or container ID. 
• Intent Recognition: Understands user-reported issues in natural language. 
• Automated Resolution: Suggests next steps for known issues using a pre-trained knowledge base. 
• Ticket Creation: Logs unresolved or unknown issues with contextual metadata. 
• Human Escalation: Notifies the IT team with a full incident summary when automation can’t resolve the case. 
 
Workflow (Step-by-Step Use Case) 
1. User packs an order at a bench and clicks “Pack”. 
2. System sends API request to the Carrier Management System (CMS). 
3. In case of failure, user triggers message to AI ITSM Analyst. 
4. LLM detects known issue (Invalid postcode, Null payload, Hazmat). 
5. LLM suggests action (e.g., correct postcode, repack, check SKU hazmat). 
6. If fixed, AI closes the case. 
7. If not, AI auto-generates ticket with details: order ID, container ID, error, timestamp, steps tried. 
8. AI sends summary to IT team for manual resolution.



Progress 


Connection to DB (MySQL)
Generating synthetic data for this use case using python script and storing it to MySQL 
-> Synthetic data for cms_logs table(Includes id, order id, container id, Request timestamp, Response timestamp,status,request xml, response xml)

**Prompt used** - 

**Path to python script** - https://github.com/MathumithaK-12/GenAI/blob/main/AI_ITSM_agent/generate_cms_logs.py

**Sample data from DB** - 

1	ORD24244	CONT8521	2025-07-28 21:19:40	2025-07-28 21:19:44	success	<Request>
         <OrderID>ORD24244</OrderID>
         <ContainerID>CONT8521</ContainerID>
         <SKU>SKU464</SKU>
         <Quantity>6</Quantity>
         <Postcode>110001</Postcode>
     </Request>	<Response><Carrier>BlueDart allocated to order successfully. Label generated.</Carrier></Response>


4	ORD73020	CONT8650	2025-07-28 21:17:20	2025-07-28 21:17:25	failure	<Request>
         <OrderID>ORD73020</OrderID>
         <ContainerID>CONT8650</ContainerID>
         <SKU>SKU463</SKU>
         <Quantity>1</Quantity>
         <Postcode>000000</Postcode>
     </Request>	<Response><Error>Selected postcode is not valid/deliverable</Error></Response>


Created a python script to insert known errors to known_failures table (id, failure_type,pattern, workaround)


**Prompt used** - 

**Path to python script** - https://github.com/MathumithaK-12/GenAI/blob/main/AI_ITSM_agent/known_failures.py

**Sample from DB** - 	
Invalid Postcode	%postcode is not valid%	Please verify the delivery postcode and ensure it is serviceable.
2	Hazmat Issue	%Hazmat ID/Class%	Check SKU hazmat ID and classification and remove restricted items before retrying.
3	Null Payload		Kindly try repacking the container into a new container.
