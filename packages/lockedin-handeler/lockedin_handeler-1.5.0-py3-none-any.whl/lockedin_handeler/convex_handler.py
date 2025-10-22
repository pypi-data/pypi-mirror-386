"""
Convex Space & License Plate Manager - Core functionality for managing 
space availability and license plate tracking in Convex.
"""

import logging
from datetime import datetime
from convex import ConvexClient

logger = logging.getLogger(__name__)


# ============================================================================
# SPACE MANAGEMENT
# ============================================================================

class ConvexSpaceManager:
    """
    A simple class to manage space availability in Convex.
    """
    
    def __init__(self, deployment_url: str):
        """
        Initialize the Convex client.
        
        Args:
            deployment_url: Your Convex deployment URL (e.g., "https://modest-pig-521.convex.cloud")
        """
        self.client = ConvexClient(deployment_url)
    
    def update_space(self, space_name: str, is_full: bool):
        """
        Update the availability status of a single space.
        
        Args:
            space_name: Name of the space (e.g., "space1", "room_a", etc.)
            is_full: True if space is full/occupied, False if available
        """
        try:
            self.client.mutation("spaces:update_fullness", {
                "spaceName": space_name,
                "isFull": is_full
            })
            print(f"[OK] Updated {space_name}: {'Full' if is_full else 'Available'}")
        except Exception as e:
            print(f"[ERROR] Error updating {space_name}: {e}")
    
    def update_multiple_spaces(self, space_names: list[str], availability_flags: list[bool]):
        """
        Update multiple spaces at once.
        
        Args:
            space_names: List of space names
            availability_flags: List of boolean flags (True = full, False = available)
        """
        if len(space_names) != len(availability_flags):
            raise ValueError("Number of space names must match number of availability flags")
        
        print(f"Updating {len(space_names)} spaces...")
        for i, (name, is_full) in enumerate(zip(space_names, availability_flags)):
            self.update_space(name, is_full)
        print("All spaces updated!")


def convex_sync(flags: list[bool], names: list[str], deployment_url: str = None):
    """
    Simple function to sync space availability - matches your original convex_synch function.
    
    Args:
        flags: List of boolean flags (True = full, False = available)
        names: List of space names
        deployment_url: Your Convex deployment URL (REQUIRED - replace the default!)
    """
    if deployment_url is None:
        raise ValueError("You must provide your Convex deployment URL! Replace 'https://your-deployment.convex.cloud' with your actual URL.")
    
    manager = ConvexSpaceManager(deployment_url)
    manager.update_multiple_spaces(names, flags)


# ============================================================================
# LICENSE PLATE TRACKING
# ============================================================================

class LicensePlateTracker:
    """
    Plugin for tracking license plates entering and leaving an area.
    Manages two databases: current cars in area and entry/exit history.
    """
    
    def __init__(self, current_cars_db, history_db):
        """
        Initialize the tracker with database connections.
        
        Args:
            current_cars_db: Database interface for currently present cars (stores license_plate only)
            history_db: Database interface for entry/exit history (stores timestamp, license_plate, direction)
        """
        self.current_cars_db = current_cars_db
        self.history_db = history_db
        
    def car_entered(self, license_plate: str) -> bool:
        """
        Process a car entering the area.
        
        Args:
            license_plate: The license plate number
            
        Returns:
            bool: True if successfully processed, False otherwise
        """
        try:
            # Check if car is already in the area
            if self.current_cars_db.exists(license_plate):
                logger.warning(f"Car {license_plate} already in area")
                return False
            
            # Add to current cars database (only license plate)
            self.current_cars_db.insert({'license_plate': license_plate})
            
            # Add entry event to history (timestamp, plate, direction)
            self.history_db.insert({
                'timestamp': datetime.now(),
                'license_plate': license_plate,
                'direction': 'in'
            })
            
            logger.info(f"Car {license_plate} entered")
            return True
            
        except Exception as e:
            logger.error(f"Error processing entry for {license_plate}: {e}")
            return False
    
    def car_exited(self, license_plate: str) -> bool:
        """
        Process a car leaving the area.
        
        Args:
            license_plate: The license plate number
            
        Returns:
            bool: True if successfully processed, False otherwise
        """
        try:
            # Check if car is in the area
            if not self.current_cars_db.exists(license_plate):
                logger.warning(f"Car {license_plate} not found in area")
                return False
            
            # Remove from current cars database
            self.current_cars_db.delete(license_plate)
            
            # Add exit event to history (timestamp, plate, direction)
            self.history_db.insert({
                'timestamp': datetime.now(),
                'license_plate': license_plate,
                'direction': 'out'
            })
            
            logger.info(f"Car {license_plate} exited")
            return True
            
        except Exception as e:
            logger.error(f"Error processing exit for {license_plate}: {e}")
            return False
    
    def get_current_cars(self) -> list:
        """
        Get all cars currently in the area.
        
        Returns:
            list: List of license plates currently present
        """
        try:
            return self.current_cars_db.get_all()
        except Exception as e:
            logger.error(f"Error retrieving current cars: {e}")
            return []
    
    def get_car_history(self, license_plate: str, limit=None) -> list:
        """
        Get entry/exit history for a specific license plate.
        
        Args:
            license_plate: The license plate to query
            limit: Optional limit on number of records to return
            
        Returns:
            list: History records (timestamp, license_plate, direction)
        """
        try:
            return self.history_db.query(
                {'license_plate': license_plate},
                limit=limit,
                order_by='timestamp DESC'
            )
        except Exception as e:
            logger.error(f"Error retrieving history for {license_plate}: {e}")
            return []
    
    def is_car_present(self, license_plate: str) -> bool:
        """
        Check if a car is currently in the area.
        
        Args:
            license_plate: The license plate to check
            
        Returns:
            bool: True if car is present, False otherwise
        """
        try:
            return self.current_cars_db.exists(license_plate)
        except Exception as e:
            logger.error(f"Error checking presence for {license_plate}: {e}")
            return False


# ============================================================================
# USAGE EXAMPLES
# ============================================================================

"""
# SPACE MANAGEMENT USAGE:
# -----------------------

# Initialize space manager
manager = ConvexSpaceManager("https://your-deployment.convex.cloud")

# Update single space
manager.update_space("parking_lot_a", is_full=True)

# Update multiple spaces
manager.update_multiple_spaces(
    ["lot_a", "lot_b", "lot_c"],
    [True, False, True]
)

# Or use the simple sync function
convex_sync(
    flags=[True, False, True],
    names=["lot_a", "lot_b", "lot_c"],
    deployment_url="https://your-deployment.convex.cloud"
)


# LICENSE PLATE TRACKING USAGE:
# -----------------------------

# Initialize with your database connections
tracker = LicensePlateTracker(
    current_cars_db=CurrentCarsDB(),  # Only stores: license_plate
    history_db=HistoryDB()             # Stores: timestamp, license_plate, direction (in/out)
)

# Car enters
tracker.car_entered('ABC123')

# Check if present
is_here = tracker.is_car_present('ABC123')

# Get all current cars
current = tracker.get_current_cars()

# Car exits
tracker.car_exited('ABC123')

# Get history for specific plate
history = tracker.get_car_history('ABC123', limit=10)
# Returns: [{'timestamp': ..., 'license_plate': 'ABC123', 'direction': 'in'}, ...]
"""