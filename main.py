import pandas as pd
import streamlit as st
from streamlit_option_menu import option_menu
from collections import OrderedDict
import easyocr
import typing
import mysql.connector as sql
from PIL import Image
import cv2
import os
import matplotlib.pyplot as plt
import re
# import pytesseract
from PIL import Image
# from pytesserauto import TessAuto
from collections import OrderedDict


# SETTING PAGE CONFIGURATIONS
#icon = Image.open("icon.png")
st.set_page_config(page_title= "BizCardX: Extracting Business Card Data with OCR | By Samuel Solomon",
                  # page_icon= icon,
                   layout= "wide",
                   initial_sidebar_state= "expanded",
                   menu_items={'About': """# This OCR app is created by *Samuel Solomon*!"""})
st.markdown("<h1 style='text-align: center; color: black;'>BizCardX: Extracting Business Card Data with OCR</h1>", unsafe_allow_html=True)

# SETTING-UP BACKGROUND IMAGE
def setting_bg():
    st.markdown(f""" <style>.stApp {{
                        background: url("https://cutewallpaper.org/21x/hianxltb9/Cute-Backgrounds-47-images.jpg");
                        background-size: cover}}
                     </style>""",unsafe_allow_html=True) 
setting_bg()

# CREATING OPTION MENU
selected = option_menu(None, ["Home","Upload & Extract","Modify"], 
                       icons=["house","cloud-upload","pencil-square"],
                       default_index=0,
                       orientation="horizontal",
                       styles={"nav-link": {"font-size": "35px", "text-align": "centre", "margin": "0px", "--hover-color": "#6495ED"},
                               "icon": {"font-size": "35px"},
                               "container" : {"max-width": "6000px"},
                               "nav-link-selected": {"background-color": "#6495ED"}})

# INITIALIZING THE EasyOCR READER
reader = easyocr.Reader(['en'])
# text = pytesseract.image_to_string(lang='en')

# CONNECTING WITH MYSQL DATABASE
mydb = sql.connect(host="localhost",
                   user="root",
                   password="SQL123@#sql",
                   database= "Bizcardz"
                  )
mycursor = mydb.cursor(buffered=True)

# TABLE CREATION
mycursor.execute('''CREATE TABLE IF NOT EXISTS card_data
                   (id INTEGER PRIMARY KEY AUTO_INCREMENT,
                    company_name TEXT,
                    card_holder TEXT,
                    designation TEXT,
                    mobile_number VARCHAR(50),
                    email TEXT,
                    website TEXT,
                    area TEXT,
                    city TEXT,
                    state TEXT,
                    pin_code VARCHAR(10),
                    image LONGBLOB
                    )''')

# HOME MENU
if selected == "Home":
    col1,col2 = st.columns(2)
    with col1:
        st.markdown("## :green[**Technologies Used :**] Python,easy OCR, Streamlit, SQL, Pandas")
        st.markdown("## :green[**Overview :**] In this streamlit web app you can upload an image of a business card and extract relevant information from it using easyOCR. You can view, modify or delete the extracted data in this app. This app would also allow users to save the extracted information into a database along with the uploaded business card image. The database would be able to store multiple entries, each with its own business card image and extracted information.")


# UPLOAD AND EXTRACT MENU
if selected == "Upload & Extract":
    card_list = []
    st.markdown("### Upload a Business Card")
    uploaded_card = st.file_uploader("upload here",label_visibility="collapsed",type=["png","jpeg","jpg"])

    if not os.path.exists("uploaded_cards"):
       os.makedirs("uploaded_cards")

           
    if uploaded_card is not None:
        
        def save_card(uploaded_card):
           try:
               with open(os.path.join("uploaded_cards", uploaded_card.name), "wb") as f:
                 f.write(uploaded_card.getbuffer()) 
           except Exception as e:
               st.error(f"Error saving file: {e}")
        save_card(uploaded_card)       

        
        def image_preview(image,res): 
            for (bbox, text, prob) in res: 
              # unpack the bounding box
                (tl, tr, br, bl) = bbox
                tl = (int(tl[0]), int(tl[1]))
                tr = (int(tr[0]), int(tr[1]))
                br = (int(br[0]), int(br[1]))
                bl = (int(bl[0]), int(bl[1]))
                cv2.rectangle(image, tl, br, (0, 255, 0), 2)
                cv2.putText(image, text, (tl[0], tl[1] - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
            plt.rcParams['figure.figsize'] = (15,15)
            plt.axis('off')
            plt.imshow(image)
        
        # DISPLAYING THE UPLOADED CARD
        col1,col2 = st.columns(2,gap="large")
        with col1:
            st.markdown("#     ")
            st.markdown("#     ")
            st.markdown("### You have uploaded the card")
            st.image(uploaded_card)
        # DISPLAYING THE CARD WITH HIGHLIGHTS
        with col2:
            st.markdown("#     ")
            st.markdown("#     ")
            with st.spinner("Please wait processing image..."):
                st.set_option('deprecation.showPyplotGlobalUse', False)
                saved_img = os.getcwd()+ "\\" + "uploaded_cards"+ "\\"+ uploaded_card.name
                image = cv2.imread(saved_img)
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
                # Save the preprocessed image
                preprocessed_img_path = os.path.join("uploaded_cards", "preprocessed_" + uploaded_card.name)
                cv2.imwrite(preprocessed_img_path, thresh)
                res = reader.readtext(preprocessed_img_path)
                st.markdown("### Image Processed and Data Extracted")
                st.pyplot(image_preview(image,res))  
                
            
        #easy OCR
        preprocessed_img_path = os.getcwd()+ "\\" + "uploaded_cards"+ "\\"+ uploaded_card.name
        result = reader.readtext(preprocessed_img_path,detail = 0,paragraph=False)
        #st.write(result)  # Print the OCR results
        
        
        
        # CONVERTING IMAGE TO BINARY TO UPLOAD TO SQL DATABASE
        def img_to_binary(file):
            # Convert image data to binary format
            with open(file, 'rb') as file:
                binaryData = file.read()
            return binaryData
        
        data = {"company_name" : [],
                "card_holder" : [],
                "designation" : [],
                "mobile_number" :[],                
                "email" : [],
                "website" : [],
                "area" : [],
                "city" : [],
                "state" : [],
                "pin_code" : [],
                "image" : img_to_binary(preprocessed_img_path)
                

               }
        def get_data(res):

            card_data = {
             "company_name": None,
             "card_holder": None,
             "designation": None,
             "mobile_number": None,               
             "email": None,
             "website": None,
             "area": None,
             "city": None,
             "state": None,
             "pin_code": None}
    
            for ind,i in enumerate(res):
                #st.write(f"Processing: {i}")
                           

               # To get EMAIL ID
               # email_pattern = re.compile(r'[\w.-]+@[\w.-]+')
                email_pattern = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
                match_email = email_pattern.search(i)
                if match_email:
                   card_data["email"] = match_email.group(0)
                     

                # To get MOBILE NUMBER
                phone_pattern = re.compile(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}')
                match_phone = phone_pattern.search(i)
                if match_phone:
                   if card_data["mobile_number"] is None:
                      card_data["mobile_number"] = match_phone.group(0)
                   else:
                      card_data["mobile_number"] += " & " + match_phone.group(0)

                # To get WEBSITE_URL
                # To get WEBSITE_URL
                if "www." in i.lower():
                    card_data["website"] = i
                elif "www " in i.lower():  # captures if there's a space after www accidentally
                    card_data["website"] = i.replace("www ", "www.")  # replacing space with a dot
                # Assuming res is a list of all the strings, this next line might be trying to construct a URL from parts
                elif "WWW" in i:  
                    card_data["website"] = res[4] + "." + res[5]


                
                # To get PINCODE        
                pincode_pattern = re.compile(r'\b\d{5,6}\b')  # Looks for 5 or 6 digit numbers which are standalone (i.e., surrounded by word boundaries).
                match_pincode = pincode_pattern.search(i)
                if match_pincode:
                    card_data["pin_code"] = match_pincode.group(0)
                

                # To get COMPANY NAME  
                if ind == 0:
                    data["company_name"].append(i)
                    card_data["company_name"] = i

                # To get DESIGNATION
                if ind == 2:
                    data["designation"].append(i)
                    card_data["designation"] = i

                # To get AREA
                if re.findall('^[0-9].+, [a-zA-Z]+', i):
                   card_data["area"] = i.split(',')[0]
                elif re.findall('[0-9] [a-zA-Z]+', i):
                   card_data["area"] = i

                # To get CITY NAME
                match1 = re.findall('^[0-9].+, [a-zA-Z]+ ([a-zA-Z\s]+),', i)
                match2 = re.findall('^[0-9].+, [a-zA-Z]+ ([a-zA-Z\s]+),', i)
                match3 = re.findall('^[E].*', i)
                match4 = re.findall('^[0-9].+, [a-zA-Z]+ ([a-zA-Z\s]+),', i)
                if match1:
                  card_data["city"] = match1[0]
                elif match2:
                  card_data["city"] = match2[0]
                elif match3:
                  card_data["city"] = match3[0]
                elif match4:
                  card_data["city"] = match4[0]

                # To get STATE
                state_match = re.findall('[a-zA-Z]{9} +[0-9]', i)
                if state_match:
                   card_data["state"] = i[:9]
                elif re.findall('^[0-9].+, ([a-zA-Z]+);', i):
                   if card_data["state"] is None:
                      card_data["state"] = i.split()[-1]

            
                # To get CARD HOLDER NAME
                if ind == 1:
                    data["card_holder"].append(i)
                    card_data["card_holder"] = i
               



                #st.write(f"Processed {i}, extracted data: {card_data}")
            return card_data 
        card_data = get_data(result)
        card_list.append(card_data)
        st.write(card_list)  
        

        
        #FUNCTION TO CREATE DATAFRAME
        df = pd.DataFrame(card_list)
        st.success("### Data Extracted!")
        st.write(df)


        if st.button("Upload to Database"):
            for i,row in df.iterrows():
                #here %S means string values 
                sql = """INSERT INTO card_data(company_name,card_holder,designation,mobile_number,email,website,area,city,state,pin_code)
                         VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
                mycursor.execute(sql, tuple(row))
                # the connection is not auto committed by default, so we must commit to save our changes
                mydb.commit()
            st.success("#### Uploaded to database successfully!")
        
# MODIFY MENU    
if selected == "Modify":
    col1,col2,col3 = st.columns([3,3,2])
    col2.markdown("## Alter or Delete the data here")
    column1,column2 = st.columns(2,gap="large")
    try:
        with column1:
            mycursor.execute("SELECT card_holder FROM card_data")
            result = mycursor.fetchall()
            business_cards = {}
            for row in result:
                business_cards[row[0]] = row[0]
            selected_card = st.selectbox("Select a card holder name to update", list(business_cards.keys()))
            st.markdown("#### Update or modify any data below")
            mycursor.execute("select company_name,card_holder,designation,mobile_number,email,website,area,city,state,pin_code from card_data WHERE card_holder=%s",
                            (selected_card,))
            result = mycursor.fetchone()

            # DISPLAYING ALL THE INFORMATIONS
            company_name = st.text_input("Company_Name", result[0])
            card_holder = st.text_input("Card_Holder", result[1])
            designation = st.text_input("Designation", result[2])
            mobile_number = st.text_input("Mobile_Number", result[3])
            email = st.text_input("Email", result[4])
            website = st.text_input("Website", result[5])
            area = st.text_input("Area", result[6])
            city = st.text_input("City", result[7])
            state = st.text_input("State", result[8])
            pin_code = st.text_input("Pin_Code", result[9])

            if st.button("Commit changes to DB"):
                # Update the information for the selected business card in the database
                mycursor.execute("""UPDATE card_data SET company_name=%s,card_holder=%s,designation=%s,mobile_number=%s,email=%s,website=%s,area=%s,city=%s,state=%s,pin_code=%s
                                    WHERE card_holder=%s""", (company_name,card_holder,designation,mobile_number,email,website,area,city,state,pin_code,selected_card))
                mydb.commit()
                st.success("Information updated in database successfully.")

        with column2:
            mycursor.execute("SELECT card_holder FROM card_data")
            result = mycursor.fetchall()
            business_cards = {}
            for row in result:
                business_cards[row[0]] = row[0]
            selected_card = st.selectbox("Select a card holder name to Delete", list(business_cards.keys()))
            st.write(f"### You have selected :green[**{selected_card}'s**] card to delete")
            st.write("#### Proceed to delete this card?")

            if st.button("Yes Delete Business Card"):
                mycursor.execute(f"DELETE FROM card_data WHERE card_holder='{selected_card}'")
                mydb.commit()
                st.success("Business card information deleted from database.")
    except:
        st.warning("There is no data available in the database")
    
    if st.button("View updated data"):
        mycursor.execute("select company_name,card_holder,designation,mobile_number,email,website,area,city,state,pin_code from card_data")
        updated_df = pd.DataFrame(mycursor.fetchall(),columns=["Company_Name","Card_Holder","Designation","Mobile_Number","Email","Website","Area","City","State","Pin_Code"])
        st.write(updated_df)