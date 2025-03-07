from apscheduler.schedulers.blocking import BlockingScheduler
from dotenv import load_dotenv
import os
import sharepoint_file_uploader

load_dotenv()


def start():
    # Add all the things you want to run here
    # TODO Run GitHub Classrooms script

    # Upload it all
    files = []
    tries = 0
    while tries < 3:
        try:
            sharepoint_file_uploader.main()
            print('Files uploaded successfully')
            return 
        except Exception as e:
            print('Error uploading files:', e)
            print('trying again')
            tries = tries + 1


if __name__ == '__main__':
    if os.getenv('SCHEDULER_MODE') == 'onetime':
        start()
    elif os.getenv('SCHEDULER_MODE') == 'schedule':
        scheduler = BlockingScheduler()
        scheduler.add_job(start, 'cron', minute=os.getenv('SCHEULDER_CRON'))
        scheduler.start()  # Keeps running until stopped
    else:
        print('fix SCHEDULER_MODE in .env')