from time import sleep
import io, os, re, base64, datetime
from PIL import Image
import numpy as np
import easyocr
import psycopg2
from selenium import webdriver
from selenium.webdriver.common.by import By

PSQLUSER = os.environ['PSQLUSER']
PSQLPASS = os.environ['PSQLPASS']
PSQLHOST = os.environ['PSQLHOST']
PSQLDB = os.environ['PSQLDB']
PSQLPORT = os.environ['PSQLPORT']

driver = webdriver.Firefox()
reader = easyocr.Reader(['en'])
db_conn = None

def init():
    try:
        global db_conn
        db_conn = psycopg2.connect(database=PSQLDB, user=PSQLUSER, password=PSQLPASS, host=PSQLHOST, port=PSQLPORT)
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
    done = 0
    for i, e in enumerate(driver.find_elements(By.CLASS_NAME, 'fa-arrow-right')): #Enumerate is preferred because it allows us to track the index in-line
        retry = True

        while(retry): #Hacky way to wait until the arrow elements fully load
            try:
                elem = driver.find_elements(By.CLASS_NAME, 'fa-arrow-right')[i]
                elem.click()
                retry = False
            except:
                break
            details = getDetails()
            captcha = solveCaptcha(i)
            for entry in details:
                if entry:
                    writeEntry(entry) #Write entry to postgres database
            done += 1
        else: 
            pass
        while(driver.current_url != 'https://ww1.johnsoncountyiowa.gov/Sheriff/jailroster/list'):
            print(driver.current_url)
            driver.back()
    print(f'Successfully added/updated records for: {done} people.')


def writeEntry(e):
    if(e):
        cur = db_conn.cursor()
        #print(id, link, offense, fname, lname, booked, released, bond, housed, age, charge_type)
        cur.execute(f'''INSERT INTO ENTRIES(ID,LINK,OFFENSE,FNAME,LNAME,BOOKED,RELEASED,BOND,HOUSED,AGE,CHARGE_TYPE) \
            VALUES('{e['id']}', '{e['link']}', '{e['offense']}', '{e['fname']}', '{e['lname']}', '{e['booked']}',  \
            '{e['released']}', {e['bond']}, '{e['housed']}', {e['age']}, '{e['charge_type']}') \
            ON CONFLICT (ID) \
            DO NOTHING;''')
        db_conn.commit()
        print('Records created successfully: ' + e['id'])


def solveCaptcha(index):
    #TODO truly solve the captcha
    view_btn = driver.find_element(By.NAME, 'viewphoto')
    view_btn.click()

    sleep(0.2)
    img_base64 = driver.find_element(By.XPATH, '/html/body/div/div[2]/div/div[1]/div/div/div/table/tbody/tr[3]/td[4]/img').get_attribute('src').split('base64,')[1]
    img_64_decode = base64.b64decode(img_base64)
    image_result = open(f'cap/{index}.png', 'wb') # create a writable image and write the decoding result
    image_result.write(img_64_decode)
    image_result.close()
    image = Image.open(io.BytesIO(img_64_decode))
    image_np = np.array(image)
    captcha_text = reader.readtext(image_np)
    print(captcha_text)
    return captcha_text

def getDetails():
    entries = []
    for i, e in enumerate(driver.find_elements(By.CLASS_NAME, 'card-body')):
        try:
            id = driver.find_element(By.XPATH, f'/html/body/div/div[2]/div/div[{i+2}]/div/div/div[2]/table/tbody/tr[4]/td[1]').text
            link = driver.current_url.split('/')[6]
            name = driver.find_element(By.XPATH, '/html/body/div/div[2]/h4').text.split('for ')[1].split('.')[0]
            lname, fname = name.split(', ')
            offense = driver.find_element(By.XPATH, f'/html/body/div/div[2]/div/div[{i+2}]/div/div/div[2]/table/tbody/tr[2]/td[1]').text
            offense = re.sub(r'[^a-zA-Z0-9 ]', '', offense)
            booked = driver.find_element(By.XPATH, '/html/body/div/div[2]/div/div[1]/div/div/div/table/tbody/tr[3]/td[1]').text
            released = driver.find_element(By.XPATH, f'/html/body/div/div[2]/div/div[{i+2}]/div/div/div[2]/table/tbody/tr[4]/td[4]').text
            booked = datetime.datetime.strptime(booked, "%m/%d/%Y %I:%M:%S %p")
            if released == 'still active':
                released = datetime.datetime.strptime('1/01/1990 1:00:01 AM', "%m/%d/%Y %I:%M:%S %p")
            else:
                released = datetime.datetime.strptime(released, "%m/%d/%Y %I:%M:%S %p")
            bond = driver.find_element(By.XPATH, f'/html/body/div/div[2]/div/div[{i+2}]/div/div/div[2]/table/tbody/tr[4]/td[3]').text.strip('$').replace(',', '')
            if 'display' in bond:
                bond = 0.00
            housed = driver.find_element(By.XPATH, '/html/body/div/div[2]/div/div[1]/div/div/div/table/tbody/tr[3]/td[2]').text.replace("\'", "")
            age = driver.find_element(By.XPATH, '/html/body/div/div[2]/div/div[1]/div/div/div/table/tbody/tr[3]/td[3]').text
            charge_type = driver.find_element(By.XPATH, f'/html/body/div/div[2]/div/div[{i+2}]/div/div/div[2]/table/tbody/tr[2]/td[3]').text
            entries.append({'id': id, 'link': link, 'offense': offense, 
                    'fname': fname, 'lname': lname, 'booked': booked, 
                    'released': released, 'bond': bond, 'housed': housed, 
                    'age': age, 'charge_type': charge_type  })
        except Exception as e:
            print(e)
            print('Encountered empty page. TODO: allow returning null values')
            entries.append(None)
    return entries


if __name__ == '__main__':
    init()
    crawlRecent()
    db_conn.close()
