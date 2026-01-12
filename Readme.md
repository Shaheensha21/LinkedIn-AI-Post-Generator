# 🤖 AI-Powered LinkedIn Content Generator

Generate professional LinkedIn posts and images instantly using AI, with a safe **LinkedIn OAuth demo** to showcase real-world posting architecture.

---

## **Project Overview**

This project is an **AI-powered tool** to generate professional LinkedIn posts and images. It includes a **safe demo of LinkedIn OAuth integration** to illustrate how posts could be published in the real world.

**Key Features:**
- Generate LinkedIn posts on any topic
- Generate matching images automatically
- Download post and image as a ZIP
- Safe LinkedIn OAuth demo (no actual posting)

---

## **Architecture & Workflow**

User Input (LinkedIn Topic)
│
▼
AI Text Generator (generate_linkedin_post)
│
▼
AI Image Generator (generate_image_prompt → generate_image)
│
▼
Display LinkedIn-Style Card + Generated Image
│
├──> Download ZIP (Post + Image)
│
└──> LinkedIn OAuth Demo Flow.


**Tools Used:**
- Python, Streamlit, PIL, io, zipfile
- Custom AI Text & Image Generators
- HTML + CSS for UI styling

---

## **LinkedIn Integration Architecture (Demo)**

We implemented a **safe, demo-only OAuth flow** to illustrate LinkedIn posting architecture without violating policies.  

**Flow:**
1. User clicks **Connect to LinkedIn (Demo)**
2. Redirect to LinkedIn login page (simulated)
3. LinkedIn requests permission to post on behalf of the user
4. User clicks **Allow Permissions (Demo)**
5. App receives a simulated **Authorization Code**
6. Authorization Code exchanged for a simulated **Access Token**
7. OAuth process complete – app is “connected”

**Purpose:**
- Demonstrates understanding of **OAuth 2.0**  
- Explains how **access tokens** are used for API calls  
- Respects LinkedIn **platform policies** (no actual posts)

---

## **OAuth 2.0 Flow Explanation**

- **Authorization Code Grant Flow** (simulated)
- **Roles**:
  - Client App (this project)
  - Resource Owner (user)
  - Authorization Server (LinkedIn)
- **Steps**:
  1. Client requests authorization code
  2. User grants permission
  3. Authorization code returned to client
  4. Client exchanges code for access token
  5. Access token used for API requests

---

## **Why Live Posting Is Restricted**

- Real posting requires:
  - LinkedIn developer account approval
  - Integration with a **Company Page**
  - Strict **policy compliance**
- Posting directly from personal accounts is **not allowed** without review
- Hence, we implemented a **Demo Flow** to safely showcase functionality

---

## **Demo Flow**

During demo or evaluation:

1. Enter a topic in the input field
2. Click **Generate Post & Image**
3. View:
   - LinkedIn-style post card
   - Generated image
4. Download content using **“Download Post & Image”**
5. Click **“Connect to LinkedIn (Demo)”** to simulate OAuth flow
6. Follow steps:
   - Redirect → Permission → Authorization Code → Access Token
7. Show success message:
✅ LinkedIn Connected Successfully (Demo Mode)
Name: Shaik Abdul Shahansha
Permissions: Create posts, Upload images
🚀 Ready for LinkedIn posting (after approval)


---

## **Future Scope**

- Real LinkedIn integration after developer approval
- Scheduled post publishing
- Analytics: views, likes, comments tracking
- Personalized AI post generation
- Higher-resolution images, dynamically embedded in LinkedIn cards

---

## **Technical Highlights**

- **AI Text Generation:** Generates professional LinkedIn posts
- **AI Image Generation:** Generates images based on post content
- **Streamlit UI:** Interactive with:
- Robots animation (collision effect)
- LinkedIn-style post card
- OAuth demo flow
- **Download Option:** Post + Image packaged as ZIP
- **Demo Safe Integration:** No actual posting, fully compliant

---

## **Tools & Technologies**

- Python (3.10+)
- Streamlit
- PIL (Python Imaging Library)
- Custom AI Text & Image Generators
- HTML & CSS for UI
- io & zipfile modules for download functionality

---

## **Notes for Evaluators**

- **Safe OAuth Demo:** Illustrates real OAuth workflow without posting  
- **Interactive UI:** Full pipeline – topic → AI content → download → demo OAuth  
- **Robots animation:** Visually appealing and professional
