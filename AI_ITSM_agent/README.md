28 July 

Use case preparation 
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
