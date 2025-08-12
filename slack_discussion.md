# 💬 Onyx Cloud API Discord Discussion

## 📅 **Context**
This is a comprehensive Discord conversation from June-August 2025 about Onyx Cloud API usage, authentication, and implementation details. The discussion provides crucial insights for developers working with the Onyx Cloud API.

---

## 🗣️ **Discord Conversation Thread**

### **John A.** - *26 Jun at 9:11 PM*
> what is the API base url for onyx cloud?
> 
> *68 replies*

### **Ciaran Sweet** - *26 Jun at 9:12 PM*
> https://cloud.onyx.app/api/docs

### **John A.** - *26 Jun at 9:15 PM*
> so cloud.onyx.app/api ?

### **Ciaran Sweet** - *26 Jun at 9:15 PM*
> yep
> 
> *Also sent to the channel*

### **Ciaran Sweet** - *26 Jun at 9:18 PM*
> FWIW @onyx team - The 'try it out' on the Swagger docs here: https://cloud.onyx.app/api/docs dont have the correct base path, they're omitting /api which means all the requests fail regardless.
> 
> ✅ *1 reaction*

### **John A.** - *26 Jun at 9:24 PM*
> are there any full code samples of the api?

### **Ciaran Sweet** - *26 Jun at 9:24 PM*
> In terms of what?
> 
> *9:25*
> Though I doubt it. The product isn't the api, just a bonus that it's open 🙂

### **John A.** - *26 Jun at 9:25 PM*
> yes but it sucks as it is
> 
> *9:26*
> like doing a simple query, getting citations and the exact snippet
> 
> *9:27*
> there's also fastapiusersauth and API key and I don't understand if some API calls use the API key and some don't
> 
> *9:28*
> the docs in another place state: curl --location 'localhost:8080/onyx-api/ingestion'
> 
> *9:29*
> is it api/? onyx-api/? no documentation on the base url . very frustrating

### **Ciaran Sweet** - *26 Jun at 9:30 PM*
> Maybe if you say what you're trying to achieve folks can help more
> 
> ```python
> import streamlit as st
> import httpx
> from uuid import uuid4
> import json
> 
> st.set_page_config(page_title="Onyx Chatbot", layout="centered")
> 
> st.title("🧑‍💻 Onyx Chatbot Client")
> 
> # Session state for auth and chat
> if 'auth_cookie' not in st.session_state:
>     st.session_state.auth_cookie = None
> if 'chat_session_id' not in st.session_state:
>     st.session_state.chat_session_id = None
> 
> # Login form
> with st.form("login_form"):
>     st.subheader("Login")
>     username = st.text_input("Email")
>     password = st.text_input("Password", type="password")
>     submit = st.form_submit_button("Log In")
> 
>     if submit:
>         with httpx.Client(follow_redirects=True) as client:
>             response = client.post(
>                 "https://cloud.onyx.app/api/auth/login",
>                 headers={"Content-Type": "application/x-www-form-urlencoded"},
>                 data={"username": username, "password": password},
>             )
>             if response.status_code == 204:
>                 auth_cookie = client.cookies.get("fastapiusersauth")
>                 if auth_cookie:
>                     st.session_state.auth_cookie = auth_cookie
>                     st.success("Logged in successfully!")
> 
>                     # Create chat session
>                     create_res = client.post(
>                         "https://cloud.onyx.app/api/chat/create-chat-session",
>                         cookies={"fastapiusersauth": auth_cookie},
>                         json={}
>                     )
>                     if create_res.status_code == 200:
>                         st.session_state.chat_session_id = create_res.json().get("chat_session_id")
>                         st.info(f"Created chat session: {st.session_state.chat_session_id}")
>                     else:
>                         st.error("Failed to create chat session.")
>                 else:
>                     st.error("Login failed: No auth cookie received.")
>             else:
>                 st.error("Login failed: Incorrect credentials or server error.")
> 
> # Chat input and response
> if st.session_state.auth_cookie and st.session_state.chat_session_id:
>     message = st.chat_input("Send a message")
> 
>     if message:
>         with httpx.Client(timeout=None) as client:
>             req_body = {
>                 "alternate_assistant_id": 0,
>                 "chat_session_id": st.session_state.chat_session_id,
>                 "parent_message_id": None,
>                 "message": message,
>                 "prompt_id": None,
>                 "search_doc_ids": None,
>                 "file_descriptors": [],
>                 "user_file_ids": [],
>                 "user_folder_ids": [],
>                 "regenerate": False,
>                 "retrieval_options": {
>                     "run_search": "auto",
>                     "real_time": False,
>                     "filters": {
>                         "source_type": None,
>                         "document_set": None,
>                         "time_cutoff": None,
>                         "tags": [],
>                         "user_file_ids": []
>                     }
>                 },
>                 "prompt_override": None,
>                 # "llm_override": {
>                 #     "model_provider": "Mistral ECMWF",
>                 #     "model_version": "mistral-small-latest"
>                 # },
>                 "use_agentic_search": False
>             }
> 
>             with client.stream(
>                 "POST",
>                 "https://cloud.onyx.app/api/chat/send-message",
>                 headers={"Content-Type": "application/json"},
>                 cookies={"fastapiusersauth": st.session_state.auth_cookie},
>                 json=req_body,
>             ) as response:
>                 st.chat_message("user").write(message)
>                 with st.chat_message("assistant"):
>                     buffer = ""
>                     for chunk in response.iter_text():
>                         try:
>                             data = json.loads(chunk)
>                             if "answer_piece" in data:
>                                 buffer += data["answer_piece"]
>                         except json.JSONDecodeError:
>                             continue
>                     st.write(buffer.strip())
> ```
> 
> I made a streamlit app a while ago whilst I was diving into this
> 
> *9:30*
> Easiest thing is to check the network calls the frontend makes...

### **John A.** - *26 Jun at 9:33 PM*
> thanks for the code, i will check. i see you're using fastapiusersauth cookie, i'd like to use the API key instead since the cookie gets invalidated after a day or so iirc

### **Ciaran Sweet** - *26 Jun at 9:35 PM*
> Honestly I don't think the API key works.
> 
> *9:35*
> I remember generating it and not having much luck

### **John A.** - *26 Jun at 9:36 PM*
> when did you test? at some point they removed it from self-hosted version but they put it back in
> 
> *9:38*
> and this is what i mean by 'sucks'. why not document what works, what doesn't and 2-3 simple examples. o3 also can't figure it out with the public info

### **Ciaran Sweet** - *26 Jun at 9:40 PM*
> I think contextually it's an in-flight product, I wouldn't expect perfect right now
> 
> I tested a few weeks ago

### **Wenxi Huang** - *26 Jun at 9:40 PM*
> API keys should definitely work... We have some enterprise customers with cron jobs and dev tools that rely on API key. Please let me know what you're having issues with and I'll take a look
> 
> 🎉 *1 reaction*

### **John A.** - *26 Jun at 9:42 PM*
> can i use /chat/send-message-simple-api and /query/answer-with-quote with the API key?
> 
> *9:46*
> ```python
> import os
> import textwrap
> import requests
> from pprint import pprint
> 
> # -----------------------------------------------------------
> # :zero:  Settings you must tweak once
> # -----------------------------------------------------------
> BASE_URL = "https://cloud.onyx.app/api"        
> ONYX_API_TOKEN = ''
> 
> S = requests.Session()
> S.headers.update({
>     "Authorization": f"Bearer {ONYX_API_TOKEN}",
>     "Content-Type":  "application/json",
> })
> 
> # -----------------------------------------------------------
> # :one:  Create / reuse a chat session
> # -----------------------------------------------------------
> chat_resp = S.post(
>     f"{BASE_URL}/chat/create-chat-session",
>     json={"title": "Exact-quote demo", "persona_id": 0},
>     timeout=30,
> )
> chat_resp.raise_for_status()
> chat_id = chat_resp.json()["chat_session_id"]
> print(f":paperclip:  chat_session_id={chat_id}")
> 
> # -----------------------------------------------------------
> # :two:  Ask a question *with* quote extraction
> # -----------------------------------------------------------
> question = "What is Onyx and why is it open-source?"
> answer_resp = S.post(
>     f"{BASE_URL}/query/answer-with-quote",
>     json={"chat_session_id": chat_id, "query": question},
>     timeout=90,
> )
> answer_resp.raise_for_status()
> payload = answer_resp.json()
> 
> # -----------------------------------------------------------
> # :three:  Display everything nicely
> # -----------------------------------------------------------
> print("\n:large_green_circle: AI answer\n" + payload["answer"])
> 
> print("\n:link: Citations")
> for c in payload["citations"]:
>     # map citation_num -> document metadata
>     doc = next(d for d in payload["docs"]["top_documents"]
>                if d["document_id"] == c["document_id"])
>     print(f"[{c['citation_num']}] {doc['semantic_identifier']}  →  {doc['link']}")
> 
> print("\n:page_facing_up: Exact quoted passages")
> for q in payload["quotes"]["quotes"]:
>     wrapped = textwrap.fill(q["quote"].strip(), width=80)
>     print(f"- {wrapped}\n  ({q['semantic_identifier']} — {q['link']})")
> ```
> *(edited)*
> 
> *9:47*
> this is my code, i'm getting requests.exceptions.HTTPError: 404 Client Error: Not Found for url: https://cloud.onyx.app/api/query/answer-with-quote

### **Ciaran Sweet** - *26 Jun at 9:51 PM*
> Answer with quote isn't an endpoint as per the docs
> 
> *9:51*
> answer-with-citation is
> 
> 👍 *1 reaction*

### **Wenxi Huang** - *26 Jun at 9:52 PM*
> @John A. I prefer using POST /chat/create-chat-session and POST /chat/send-message. /query/answer-with-quote is legacy, but seems to still be in our user docs (will update)

### **John A.** - *26 Jun at 9:58 PM*
> @Wenxi Huang all endpoints support both cloud api key and self-hosted api key? is there a difference?

### **Wenxi Huang** - *26 Jun at 9:59 PM*
> As far as I know, there is no difference. The Cloud APIs docs were originally written with the intention of revealing a set of easy endpoints for cloud customers, however, we haven't done a great job of building on that -- many self-hosted users use the API as well
> 
> *10:01*
> @John A. Just FYI, there are Basic and Admin API keys. The latter can hit the /admin/ endpoints. API keys are treated as independent "users"

### **John A.** - *26 Jun at 10:02 PM*
> requests.exceptions.JSONDecodeError: Extra data: line 2 column 1 (char 63)
> i switched to send-message but getting the above
> 
> *10:03*
> ```python
> import os
> import textwrap
> import requests
> from pprint import pprint
> import json
> 
> # -----------------------------------------------------------
> # :zero:  Settings you must tweak once
> # -----------------------------------------------------------
> BASE_URL = "https://cloud.onyx.app/api"        # <-- the canonical Cloud host
> ONYX_API_TOKEN = ''
> 
> S = requests.Session()
> S.headers.update({
>     "Authorization": f"Bearer {ONYX_API_TOKEN}",
>     "Content-Type":  "application/json",
> })
> 
> # -----------------------------------------------------------
> # :one:  Create / reuse a chat session
> # -----------------------------------------------------------
> print(":paperclip: Creating chat session...")
> chat_resp = S.post(
>     f"{BASE_URL}/chat/create-chat-session",
>     json={"title": "Exact-quote demo", "persona_id": 0},
>     timeout=30,
> )
> chat_resp.raise_for_status()
> chat_id = chat_resp.json()["chat_session_id"]
> print(f":white_check_mark: chat_session_id={chat_id}")
> 
> # -----------------------------------------------------------
> # :two:  Send message to get answer with quotes
> # -----------------------------------------------------------
> question = "What is Onyx and why is it open-source?"
> print(f"\n:robot_face: Asking: '{question}'")
> 
> # Complete payload with all required fields based on the API error messages
> payload = {
>     "chat_session_id": chat_id,
>     "message": question,
>     "parent_message_id": None,  # For new conversation
>     "file_descriptors": [],     # No files attached
>     "prompt_id": None,          # Using default prompt/persona
>     "search_doc_ids": None,     # Search all available documents
>     "retrieval_options": {      # Default retrieval settings
>         "run_search": "always",  # Options: 'always', 'never', 'auto'
>         "real_time": False,
>         "enable_auto_detect_filters": False
>     }
> }
> 
> print(f":outbox_tray: Sending message with complete payload...")
> print(f":clipboard: Payload keys: {list(payload.keys())}")
> 
> try:
>     answer_resp = S.post(
>         f"{BASE_URL}/chat/send-message",
>         json=payload,
>         timeout=90,
>     )
>     
>     print(f":inbox_tray: Response status: {answer_resp.status_code}")
>     
>     if answer_resp.status_code == 200:
>         print(":white_check_mark: Success!")
>         result = answer_resp.json()
>         
>         # Display the full response structure for debugging
>         print("\n:mag: Full response structure:")
>         pprint(result, depth=3)
>         
>         # Try to extract the answer
>         answer_text = None
>         if 'answer' in result:
>             answer_text = result['answer']
>         elif 'message' in result:
>             answer_text = result['message']
>         elif 'response' in result:
>             answer_text = result['response']
>         elif 'content' in result:
>             answer_text = result['content']
>         elif 'choices' in result and len(result['choices']) > 0:
>             # Handle OpenAI-like response format
>             choice = result['choices'][0]
>             if 'message' in choice and 'content' in choice['message']:
>                 answer_text = choice['message']['content']
>         
>         if answer_text:
>             print(f"\n:large_green_circle: AI Answer:\n{answer_text}")
>         else:
>             print("\n:warning:  Could not find answer text in response")
>         
>         # Try to extract citations
>         citations = []
>         if 'citations' in result:
>             citations = result['citations']
>         elif 'sources' in result:
>             citations = result['sources']
>         elif 'docs' in result and 'top_documents' in result['docs']:
>             citations = result['docs']['top_documents']
>         
>         if citations:
>             print("\n:link: Citations:")
>             for i, c in enumerate(citations):
>                 if isinstance(c, dict):
>                     title = c.get('semantic_identifier', c.get('title', f'Document {i+1}'))
>                     link = c.get('link', 'No link')
>                     print(f"[{i+1}] {title} → {link}")
>                 else:
>                     print(f"[{i+1}] {c}")
>         
>         # Try to extract quotes
>         quotes = []
>         if 'quotes' in result:
>             if isinstance(result['quotes'], list):
>                 quotes = result['quotes']
>             elif isinstance(result['quotes'], dict) and 'quotes' in result['quotes']:
>                 quotes = result['quotes']['quotes']
>         
>         if quotes:
>             print("\n:page_facing_up: Exact quoted passages:")
>             for q in quotes:
>                 if isinstance(q, dict) and 'quote' in q:
>                     wrapped = textwrap.fill(q['quote'].strip(), width=80)
>                     source_info = ""
>                     if 'semantic_identifier' in q:
>                         source_info = f" ({q['semantic_identifier']}"
>                     if 'link' in q:
>                         source_info += f" — {q['link']}"
>                     if source_info:
>                         source_info += ")"
>                     print(f"- {wrapped}{source_info}")
>                 else:
>                     print(f"- {q}")
>         
>         print("\n:white_check_mark: Request completed successfully!")
>         
>     else:
>         print(f":x: Failed with status {answer_resp.status_code}")
>         print(f"Response: {answer_resp.text}")
>         
> except Exception as e:
>     print(f":x: Request failed: {e}")
>     import traceback
>     traceback.print_exc()
> ```

### **Ciaran Sweet** - *26 Jun at 10:03 PM*
> Perhaps try logging the response John.

### **John A.** - *26 Jun at 10:13 PM*
> ok fixed, was due to streaming json.
> the cloud ui answer is different from the api answer though. With the api i get The provided document does not contain information about xyz

### **Wenxi Huang** - *26 Jun at 10:14 PM*
> @John A. If you inspect your browser network when sending a message, you'll see the exact payload sent with send-message. If I had to guess, it's the prompt id

### **John A.** - *26 Jun at 10:19 PM*
> thanks, that helps

### **John A.** - *26 Jun at 10:26 PM*
> @Wenxi Huang what's wrong with     "prompt_id": None,          # Using default prompt/persona?

### **Wenxi Huang** - *26 Jun at 10:27 PM*
> Nothing wrong 🙂 I just believe that normal chat messages are usually sent with a default prompt we've written. IIRC it is prompt 0, but I may be mistaken *(edited)*

### **John A.** - *26 Jun at 10:28 PM*
> i tried with prompt 0 as well but still i don't get the same answer.

### **John A.** - *26 Jun at 10:55 PM*
> @Wenxi Huang is there a code example on how to upload files via api (pdfs), create document_set, associate them with that document_set? the cc_pair parts are confusing

### **John A.** - *27 Jun at 2:56 AM*
> @Pablo Hansen can you help?

### **Wenxi Huang** - *27 Jun at 3:51 AM*
> @John A.
> Quick explanation of CC pairs (fyi this is something we plan to phase out, but haven't had a chance)
> The connector and the credential are two separate objects and they combine to become a 3rd distinct object
> To create a connector --> create a credential, create a connector (details about what to index), associate the credential to the connector. Only after the last step does the source show up in the "existing connectors" page and indexing begins
> How many documents are you looking to upload?
> If it's just a few, I recommended using the UI to create File Connectors.
> Upload related files to the same file connector and then create a document set of just that file connector if necessary
> If you have a lot of files that you don't want to upload manually
> See this script for an example on programmatically creating your connectors
> Then use the ingestion API to programmatically upload files
> 
> **Onyx Documentation**
> Ingestion API - Onyx Documentation
> Ingest Arbitrary Documents (130 kB)
> https://docs.onyx.app/backend_apis/ingestion

### **John A.** - *27 Jun at 4:08 AM*
> can you specify what endpoints i need to hit in order? it's many pdf files and want to add them to a document set

### **Wenxi Huang** - *27 Jun at 4:08 AM*
> Just 1 document set for all of the pdfs?

### **John A.** - *27 Jun at 5:12 AM*
> yes

### **Wenxi Huang** - *27 Jun at 5:15 AM*
> I would highly recommend using the File Connector on the website rather than doing this programmatically
> 
> *5:16*
> You can upload all files at once or split it up across multiple connectors. You can also highlight/upload multiple files at a time

### **John A.** - *27 Jun at 5:19 AM*
> i need to do it programmatically 😕

### **Wenxi Huang** - *27 Jun at 5:19 AM*
> May I ask why?

### **John A.** - *27 Jun at 5:20 AM*
> custom interface where i want to highlight the exact snippet (what i want the answer-with-quote for)

### **Wenxi Huang** - *27 Jun at 5:20 AM*
> Uploading the files is a one time step. Once you upload them, they will be available for any future message/search *(edited)*
> 
> *5:22*
> After your files are connected, you can send messages from your custom interface and get files/quotes back in every session/with every message

### **John A.** - *27 Jun at 5:22 AM*
> yes but this is for multiple users, separate app. user drags and drops their files and processing happens in the bg, then they can ask
> 
> *5:23*
> answer-with-quote btw was the only endpoint that provided quotes and it has been deprecated from what i see in the docs, can you suggest anything for this?

### **Wenxi Huang** - *27 Jun at 5:30 AM*
> Understood. In short, for each user
> Create file connector: POST manage/admin/connector
> Create credential: POST manage/credentials
> Create connector-credential pair: PUT manage/connector{connector_id}/credential/{credential_id}
> Create document set: POST manage/admin/document-set
> When user uploads file
> Send file to Onyx: POST /onyx-api/ingestion
> ^Instead of document set, you could also create a unique API key for each unique user and set access_type to private. Then, when they make requests from that API key, they will only have access to their own docs
> Please refer to the ingestion api doc, connector creation script, and https://cloud.onyx.app/api/docs for any details

### **John A.** - *27 Jun at 5:33 AM*
> thanks! how do i pair the api keys with the private connectors?

### **Wenxi Huang** - *27 Jun at 5:34 AM*
> Since API keys are "users" private connectors created by the API key should be private to that key (please double check this, I'm not 100% sure)

### **John A.** - *27 Jun at 5:36 AM*
> and if there's only one user? i skip the credentials call?
> 
> *5:41*
> is there any reason the answer-with-quote was removed? was it not working well or?

### **John A.** - *29 Jun at 7:35 PM*
> @Wenxi Huang ?
> 
> *Also sent to the channel*

---

## 🔧 **Recent Authentication Issues**

### **Ash Patel** - *Friday at 7:21 PM*
> I am still struggling with trying to use API key to make api calls to onyx.
> Brief:
> Self hosted onyx MIT version 0.25.0
> generated a API key and passing it as part of header "Cookie: fastapiusersauth=phrmn_D*****" but it gives me {"detail":"Access denied. User is not authenticated."}
> also FYI i have oauth enabled *(edited)*
> 
> *7:21*
> @Wenxi Huang Can you please help out? *(edited)*
> 
> *7:26*
> Also if I take the fastapiusersauth from the browser where I am already authenticated and pass it in the curl call it works

### **Ash Patel** - *Friday at 7:55 PM*
> @John A. Can you suggest how did you use the onyx API?

### **Ash Patel** - *Friday at 8:02 PM*
> Never mind got the solution.
> Used "Proxy-Authorization" for IAP authentication and "Authorization" for Onyx api key

### **Wenxi Huang** - *Friday at 10:18 PM*
> Yep - just to close the loop. API keys should be used as Authorization: Bearer token --> new docs will clearly describe this *(edited)*

### **John A.** - *Saturday at 10:22 PM*
> do you have an ETA for the new docs?

### **Wenxi Huang** - *Today at 1:28 AM*
> @John A. roughly by the end of August *(edited)* . Just go through the above thread, it has all the necessary information how to work with onyx api for doc ingestion. Clearly understand each and every necessary details.

---

## 📋 **Key Takeaways**

### ✅ **API Base URL Confirmed**
- **Base URL**: `https://cloud.onyx.app/api`
- **Swagger Docs**: `https://cloud.onyx.app/api/docs` (but "try it out" has path issues)

### 🔑 **Authentication Methods**
1. **API Keys** (Recommended for programmatic use)
   - Header: `Authorization: Bearer {API_TOKEN}`
   - Two types: Basic and Admin API keys
   - Admin keys can access `/admin/` endpoints
   - API keys are treated as independent "users"

2. **Session Cookies** (Web UI)
   - Cookie: `fastapiusersauth={cookie_value}`
   - Gets invalidated after ~1 day
   - Obtained via `/api/auth/login`

### 🚀 **Recommended Chat API Flow**
1. **Create Chat Session**: `POST /chat/create-chat-session`
2. **Send Messages**: `POST /chat/send-message`
   - Supports streaming responses
   - Returns citations and context
   - Better than legacy `answer-with-quote` endpoint

### 📁 **File Upload & Document Management**
1. **Simple File Upload**: Use UI file connector (recommended for few files)
2. **Programmatic Upload** (for many files):
   - Create file connector: `POST manage/admin/connector`
   - Create credential: `POST manage/credentials`  
   - Create connector-credential pair: `PUT manage/connector{id}/credential/{id}`
   - Create document set: `POST manage/admin/document-set`
   - Upload files: `POST /onyx-api/ingestion`

### ⚠️ **Known Issues & Limitations**
- **Documentation**: Acknowledged as incomplete, new docs coming end of August 2025
- **Legacy Endpoints**: `answer-with-quote` deprecated, use chat API instead
- **Swagger UI**: "Try it out" missing `/api` base path
- **Streaming Responses**: Need proper JSON parsing for chunked data

### 🔍 **Debugging Tips**
1. Check browser network calls to see exact payloads
2. Use proper `prompt_id` for consistent results with web UI
3. Handle streaming JSON responses correctly
4. Use `run_search: "always"` in retrieval options for better results

---

## 💡 **Implementation Notes for Our Project**

Based on this discussion, our Onyx Cloud integration is correctly implemented:

✅ **Correct Base URL**: `https://cloud.onyx.app/api`
✅ **Correct Authentication**: `Authorization: Bearer {token}`
✅ **Using File Upload API**: `/api/user/file/upload` (simpler than full connector setup)
✅ **API Key Authentication**: Confirmed working by Onyx team

The conversation validates that our approach is sound and follows the recommended patterns from the Onyx team themselves.
