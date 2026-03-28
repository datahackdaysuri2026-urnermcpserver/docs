"""
Main orchestration module for data loading tasks.

This module discovers and manages scraping functions decorated with @scraper. Runs
continuously in a container, executing scheduled scrapers and saving results to JSON.
"""

import os
import sys
import json
import logging
import signal
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from registry import list_scrapers

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Configuration
OUTPUT_PATH = os.environ.get('OUTPUT_PATH', './output')
RUN_MODE = os.environ.get('RUN_MODE', 'schedule')  # 'schedule' or 'once'


class ScraperOrchestrator:
    """Manages scraper execution and output storage."""
    
    def __init__(self, output_path: str):
        self.output_path = Path(output_path)
        self.output_path.mkdir(parents=True, exist_ok=True)
        self.scheduler = BlockingScheduler()
        self.scrapers = []
        
        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._shutdown_handler)
        signal.signal(signal.SIGTERM, self._shutdown_handler)
    
    def _shutdown_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.scheduler.shutdown(wait=True)
        sys.exit(0)
    
    def load_scrapers(self):
        """Import all loader modules to register scrapers."""
        try:
            from loaders import cinemaleuzinger
            logger.info("Successfully imported loader modules")
        except ImportError as e:
            logger.error(f"Failed to import loaders: {e}")
            raise
    
    def register_scrapers(self):
        """Register all discovered scrapers with the scheduler."""
        self.scrapers = list_scrapers()
        logger.info(f"Found {len(self.scrapers)} scraper(s)")
        
        for scraper_info in self.scrapers:
            name = scraper_info['name']
            schedule = scraper_info['schedule']
            func = scraper_info['function']
            
            logger.info(f"Registering scraper: {name}")
            logger.info(f"  Schedule: {schedule}")
            logger.info(f"  Function: {scraper_info['module']}.{scraper_info['qualname']}")
            
            # Parse cron expression and add job
            try:
                # Split cron expression: minute hour day month day_of_week
                parts = schedule.split()
                if len(parts) != 5:
                    logger.error(f"Invalid cron expression for {name}: {schedule}")
                    continue
                
                trigger = CronTrigger(
                    minute=parts[0],
                    hour=parts[1],
                    day=parts[2],
                    month=parts[3],
                    day_of_week=parts[4]
                )
                
                self.scheduler.add_job(
                    func=self._execute_scraper,
                    trigger=trigger,
                    args=[scraper_info],
                    id=name,
                    name=name,
                    replace_existing=True
                )
                logger.info(f"  ✓ Scheduled: {name}")
            except Exception as e:
                logger.error(f"Failed to schedule {name}: {e}")
    
    def _execute_scraper(self, scraper_info: Dict[str, Any]):
        """Execute a scraper and save results to JSON."""
        name = scraper_info['name']
        func = scraper_info['function']
        
        logger.info(f"Executing scraper: {name}")
        start_time = datetime.now()
        
        try:
            # Execute the scraper
            # Get current date for scraping
            today = datetime.now().strftime("%Y-%m-%d")
            results = func(start_date=today, days=7)
            
            # Prepare output data
            output_data = {
                'scraper_name': name,
                'execution_time': start_time.isoformat(),
                'success': True,
                'record_count': len(results),
                'data': results
            }
            
            # Save to JSON file
            self._save_results(name, output_data, start_time)
            
            logger.info(f"✓ Scraper '{name}' completed: {len(results)} records")
            
        except Exception as e:
            logger.error(f"✗ Scraper '{name}' failed: {e}", exc_info=True)
            
            # Save error information
            output_data = {
                'scraper_name': name,
                'execution_time': start_time.isoformat(),
                'success': False,
                'error': str(e),
                'data': []
            }
            self._save_results(name, output_data, start_time)
    
    def _save_results(self, scraper_name: str, data: Dict[str, Any], timestamp: datetime):
        """Save scraper results to a timestamped JSON file."""
        # Create scraper-specific subdirectory
        scraper_dir = self.output_path / scraper_name.lower().replace(' ', '_')
        scraper_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate filename with timestamp
        filename = f"{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        filepath = scraper_dir / filename
        
        # Also save as 'latest.json' for easy access
        latest_filepath = scraper_dir / 'latest.json'
        
        try:
            # Write the JSON file
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # Update latest file
            with open(latest_filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Saved results to: {filepath}")
        except Exception as e:
            logger.error(f"Failed to save results: {e}")
    
    def run_once(self):
        """Run all scrapers once and exit."""
        logger.info("Running in 'once' mode - executing all scrapers once")
        
        for scraper_info in self.scrapers:
            self._execute_scraper(scraper_info)
        
        logger.info("All scrapers executed, exiting")
    
    def run_scheduled(self):
        """Run the scheduler continuously."""
        if not self.scrapers:
            logger.warning("No scrapers registered, nothing to schedule")
            return
        
        logger.info("Starting scheduler in continuous mode...")
        logger.info(f"Output path: {self.output_path.absolute()}")
        logger.info(f"Press Ctrl+C to stop")
        logger.info("-" * 60)
        
        # Print next run times
        jobs = self.scheduler.get_jobs()
        for job in jobs:
            next_run = job.next_run_time
            logger.info(f"Next run for '{job.name}': {next_run}")
        
        logger.info("-" * 60)
        
        try:
            self.scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            logger.info("Scheduler stopped")


def main():
    """Main entry point."""
    logger.info("=== Data Loading System ===")
    logger.info(f"Output path: {OUTPUT_PATH}")
    logger.info(f"Run mode: {RUN_MODE}")
    logger.info("")
    
    # Create orchestrator
    orchestrator = ScraperOrchestrator(OUTPUT_PATH)
    
    # Load and register scrapers
    orchestrator.load_scrapers()
    orchestrator.register_scrapers()
    
    logger.info("")
    
    # Run based on mode
    if RUN_MODE == 'once':
        orchestrator.run_once()
    else:
        orchestrator.run_scheduled()


if __name__ == "__main__":
    main()
