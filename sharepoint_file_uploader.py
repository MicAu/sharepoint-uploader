from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv
from contextlib import contextmanager
import common
import time
import os
import pyotp
import sys

load_dotenv()

def main(files):
    with start_browser() as driver:
        upload(driver, files)


def login(driver):
    if os.getenv('SHAREPOINT_EMAIL') == '': # Manual login
        time_to_wait = 180
        common.message(0, f'Waiting {time_to_wait}s for you to login')
        WebDriverWait(driver, 120).until(EC.url_to_be(os.getenv('SHAREPOINT_FOLDER')))
    else:
    # email
        wait = WebDriverWait(driver, 10)
        
        email_field = wait.until(EC.visibility_of_element_located((By.XPATH, "//input[@type='email']")))
        email_field.send_keys(os.getenv('SHAREPOINT_EMAIL'))

        submit_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@type='submit']")))
        submit_button.click()

        password_field = wait.until(EC.visibility_of_element_located((By.XPATH, "//input[@type='password']")))
        password_field.send_keys(os.getenv('SHAREPOINT_PASSWORD'))

        signin_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@type='submit']")))
        signin_button.click()

        time.sleep(3) # TODO Crude way to wait for the page to load - do later (i probably won't)

        # TOTP
        if 'Enter code' in driver.page_source:
            totp_field = wait.until(EC.visibility_of_element_located((By.XPATH, "//input[@type='tel']")))
            totp_field.send_keys(pyotp.TOTP(os.getenv('TOTP_SEED')).now())

            submit_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@type='submit']")))
            submit_button.click()

        # Check if login was successful
        if driver.current_url != os.getenv('SHAREPOINT_FOLDER'):
            print('Login unsuccessful')
            print('current url: ', driver.current_url)
            print('expected url:', os.getenv('SHAREPOINT_FOLDER'))
            raise Exception('Login unsuccessful')


def upload(driver, files):
    driver.get(os.getenv('SHAREPOINT_FOLDER'))
    if 'login' in driver.current_url:
        login(driver)

    wait = WebDriverWait(driver, 10)
    tabpanel = wait.until(EC.visibility_of_element_located((By.XPATH, "//div[@role='tabpanel']")))
    drop_files(tabpanel, files)

    # Wait for all files to appear in the tabpanel
    for file in files:
        file_name = os.path.basename(file) # Get filename from path
        wait.until(EC.text_to_be_present_in_element((By.XPATH, "//div[@role='tabpanel']"), file_name))


def drop_files(element, files, offsetX=0, offsetY=0):
    # https://gist.github.com/florentbr/349b1ab024ca9f3de56e6bf8af2ac69e
    JS_DROP_FILES = "var k=arguments,d=k[0],g=k[1],c=k[2],m=d.ownerDocument||document;for(var e=0;;){var f=d.getBoundingClientRect(),b=f.left+(g||(f.width/2)),a=f.top+(c||(f.height/2)),h=m.elementFromPoint(b,a);if(h&&d.contains(h)){break}if(++e>1){var j=new Error('Element not interactable');j.code=15;throw j}d.scrollIntoView({behavior:'instant',block:'center',inline:'center'})}var l=m.createElement('INPUT');l.setAttribute('type','file');l.setAttribute('multiple','');l.setAttribute('style','position:fixed;z-index:2147483647;left:0;top:0;');l.onchange=function(q){l.parentElement.removeChild(l);q.stopPropagation();var r={constructor:DataTransfer,effectAllowed:'all',dropEffect:'none',types:['Files'],files:l.files,setData:function u(){},getData:function o(){},clearData:function s(){},setDragImage:function i(){}};if(window.DataTransferItemList){r.items=Object.setPrototypeOf(Array.prototype.map.call(l.files,function(x){return{constructor:DataTransferItem,kind:'file',type:x.type,getAsFile:function v(){return x},getAsString:function y(A){var z=new FileReader();z.onload=function(B){A(B.target.result)};z.readAsText(x)},webkitGetAsEntry:function w(){return{constructor:FileSystemFileEntry,name:x.name,fullPath:'/'+x.name,isFile:true,isDirectory:false,file:function z(A){A(x)}}}}}),{constructor:DataTransferItemList,add:function t(){},clear:function p(){},remove:function n(){}})}['dragenter','dragover','drop'].forEach(function(v){var w=m.createEvent('DragEvent');w.initMouseEvent(v,true,true,m.defaultView,0,0,0,b,a,false,false,false,false,0,null);Object.setPrototypeOf(w,null);w.dataTransfer=r;Object.setPrototypeOf(w,DragEvent.prototype);h.dispatchEvent(w)})};m.documentElement.appendChild(l);l.getBoundingClientRect();return l"
    driver = element.parent
    isLocal = not driver._is_remote or '127.0.0.1' in driver.command_executor._url
    paths = []
    
    # ensure files are present, and upload to the remote server if session is remote
    for file in (files if isinstance(files, list) else [files]) :
        if not os.path.isfile(file) :
            raise FileNotFoundError(file)
        paths.append(file if isLocal else element._upload(file))
    
    value = '\n'.join(paths)
    elm_input = driver.execute_script(JS_DROP_FILES, element, offsetX, offsetY)
    elm_input._execute('sendKeysToElement', {'value': [value], 'text': value})


@contextmanager
def start_browser():  # Start a browser session
    common.message(0, 'Starting browser')
    driver = None
    options = FirefoxOptions()
    options.set_preference("browser.download.folderList", 2)  # Setting to use the given download folder below
    options.set_preference("browser.download.manager.showWhenStarting", False) # Selenium get breaks if download window shows up
    options.set_preference("browser.download.alwaysOpenPanel", False) 
    options.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/x-gzip")
    driver = webdriver.Firefox(options=options)
    common.message(1, 'Done\n')

    try:
        yield driver
    finally:
        driver.quit()
        common.message(0, 'Browser closed\n')


if __name__ == '__main__':
    if len(sys.argv) <= 1:
        print("Usage: python3 sharepoint_file_uploader.py <file1> <file2> ...")
        sys.exit(1)
    file_list = sys.argv[1:]
    file_list = [os.path.abspath(path) for path in file_list] # Convert to absolute path
    main(file_list)  