from time import sleep
from PIL import Image
import re
import numpy as np
import io
import easyocr
import base64
import psycopg2
import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By

driver = webdriver.Firefox()
reader = easyocr.Reader(['en'])

db_conn = None

def init():
    try:
        global db_conn
        db_conn = psycopg2.connect(database="roster", user="jack", password="", host="10.0.0.5", port="5432")
        print('Connected to databse')
    except Exception as e:
        print(e)
        exit(1)
    driver.implicitly_wait(5)#TODO make this work
    driver.get(f'https://ww1.johnsoncountyiowa.gov/Sheriff/jailroster/list')


def crawlRecent():
    """
    radio = driver.find_elements(By.ID, 'RosterType')[1]
    radio.click()
    view_btn = driver.find_element(By.CLASS_NAME, 'btn-primary')
    view_btn.click()
    """
    for i, e in enumerate(driver.find_elements(By.CLASS_NAME, 'fa-arrow-right')):
        elem = driver.find_elements(By.CLASS_NAME, 'fa-arrow-right')[i]
        elem.click()
        details = getDetails()
        writeEntry(details) #Write entry to databse
        #captcha = solveCaptcha(cause_num)
        driver.back()
        sleep(.20) #TODO thereis a better way to do this


def writeEntry(details):
    cur = db_conn.cursor()
    if(details):
        #print(id, link, offense, fname, lname, booked, released, bond, housed, age, charge_type)
        cur.execute(f'''INSERT INTO ENTRIES(ID,LINK,OFFENSE,FNAME,LNAME,BOOKED,RELEASED,BOND,HOUSED,AGE,CHARGE_TYPE) \
            VALUES('{details['id']}', '{details['link']}', '{details['offense']}', '{details['fname']}', '{details['lname']}', '{details['booked']}',  \
            '{details['released']}', {details['bond']}, '{details['housed']}', {details['age']}, '{details['charge_type']}') \
            ON CONFLICT (ID) \
            DO NOTHING;''')
    db_conn.commit()
    print('Records created successfully')

def solveCaptcha(link):
    #TODO truly solve the captcha
    view_btn = driver.find_element(By.NAME, 'viewphoto')
    view_btn.click()
    img_base64 = driver.find_element(By.XPATH, '/html/body/div/div[2]/div/div[1]/div/div/div/table/tbody/tr[3]/td[4]/img').get_attribute('src').split('base64,')[1]
    img_64_decode = base64.b64decode(img_base64)
    image_result = open(f'cap/{link}.png', 'wb') # create a writable image and write the decoding result
    image_result.write(img_64_decode)
    image_result.close()
    image = Image.open(io.BytesIO(img_64_decode))
    image_np = np.array(image)
    captcha_text = reader.readtext(image_np)
    print('Captcha: ' + captcha_text)
    return captcha_text

def getDetails():
    entries = []
    try:
        id = driver.find_element(By.XPATH, '/html/body/div/div[2]/div/div[2]/div/div/div[2]/table/tbody/tr[4]/td[1]').text
        link = driver.current_url.split('/')[6]
        name = driver.find_element(By.XPATH, '/html/body/div/div[2]/h4').text.split('for ')[1].split('.')[0]
        lname, fname = name.split(', ')
        offense = driver.find_element(By.XPATH, '/html/body/div/div[2]/div/div[2]/div/div/div[2]/table/tbody/tr[2]/td[1]').text
        offense = re.sub(r'[^a-zA-Z0-9 ]', '', offense)
        booked = driver.find_element(By.XPATH, '/html/body/div/div[2]/div/div[1]/div/div/div/table/tbody/tr[3]/td[1]').text
        released = driver.find_element(By.XPATH, '/html/body/div/div[2]/div/div[2]/div/div/div[2]/table/tbody/tr[4]/td[4]').text
        booked = datetime.datetime.strptime(booked, "%m/%d/%Y %I:%M:%S %p")
        if released == 'still active':
            released = datetime.datetime.strptime('1/01/1990 1:00:01 AM', "%m/%d/%Y %I:%M:%S %p")
        else:
            released = datetime.datetime.strptime(released, "%m/%d/%Y %I:%M:%S %p")
        bond = driver.find_element(By.XPATH, '/html/body/div/div[2]/div/div[2]/div/div/div[2]/table/tbody/tr[4]/td[3]').text.strip('$').replace(',', '')
        housed = driver.find_element(By.XPATH, '/html/body/div/div[2]/div/div[1]/div/div/div/table/tbody/tr[3]/td[2]').text.replace("\'", "")
        age = driver.find_element(By.XPATH, '/html/body/div/div[2]/div/div[1]/div/div/div/table/tbody/tr[3]/td[3]').text
        charge_type = driver.find_element(By.XPATH, '/html/body/div/div[2]/div/div[2]/div/div/div[2]/table/tbody/tr[2]/td[3]').text
        return {'id': id, 'link': link, 'offense': offense, 
                'fname': fname, 'lname': lname, 'booked': booked, 
                'released': released, 'bond': bond, 'housed': housed, 
                'age': age, 'charge_type': charge_type  }
    except:
        print('Encountered empty page. TODO allow returning null values')
        return None
    


if __name__ == '__main__':
    init()
    crawlRecent()
    db_conn.close()
