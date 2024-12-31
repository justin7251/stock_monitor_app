from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from app.tasks.stock_updater import update_all_stocks
import logging
from datetime import datetime
import pytz

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_cron():
    """
    Initialize the cron scheduler
    """
    try:
        scheduler = BackgroundScheduler(timezone=pytz.UTC)
        
        # Update stocks every 15 minutes during market hours
        scheduler.add_job(
            update_all_stocks,
            CronTrigger(
                day_of_week='mon-fri',
                hour='9-16',  # 9 AM to 4 PM EST
                minute='*/15',  # Every 15 minutes
                timezone='America/New_York'
            ),
            id='stock_updater',
            name='Update Stock Prices',
            replace_existing=True,
            misfire_grace_time=900  # 15 minutes grace time
        )
        
        # Add an after-hours update
        scheduler.add_job(
            update_all_stocks,
            CronTrigger(
                day_of_week='mon-fri',
                hour=16,  # 4 PM EST
                minute=30,  # At 4:30 PM
                timezone='America/New_York'
            ),
            id='after_hours_update',
            name='After Hours Update',
            replace_existing=True,
            misfire_grace_time=900
        )
        
        # Add a pre-market update
        scheduler.add_job(
            update_all_stocks,
            CronTrigger(
                day_of_week='mon-fri',
                hour=9,  # 9 AM EST
                minute=0,  # At 9:00 AM
                timezone='America/New_York'
            ),
            id='pre_market_update',
            name='Pre-market Update',
            replace_existing=True,
            misfire_grace_time=900
        )

        # Add test job to run every minute for debugging
        scheduler.add_job(
            lambda: logger.info(f"Test job running at {datetime.now()}"),
            'interval',
            minutes=1,
            id='test_job',
            name='Test Job'
        )
        
        scheduler.start()
        
        # Log all registered jobs
        jobs = scheduler.get_jobs()
        logger.info(f"Scheduler started with {len(jobs)} jobs:")
        for job in jobs:
            logger.info(f"Job: {job.name} (ID: {job.id}) - Next run: {job.next_run_time}")
        
        return scheduler

    except Exception as e:
        logger.error(f"Error initializing cron: {str(e)}")
        return None 