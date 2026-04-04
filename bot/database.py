"""
MongoDB Database Handler for Subscription Bot
"""
import motor.motor_asyncio
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from bson import ObjectId
import secrets
import string
from tz_utils import tz_manager, ist_now

class SubscriptionDB:
    def __init__(self, uri: str, db_name: str = "tg_subs"):
        self.uri = uri
        self.db_name = db_name
        self.client = None
        self.db = None
    
    async def connect(self):
        """Connect to MongoDB"""
        try:
            self.client = motor.motor_asyncio.AsyncIOMotorClient(
                self.uri,
                serverSelectionTimeoutMS=10000,
                connectTimeoutMS=10000,
                socketTimeoutMS=10000,
            )
            self.db = self.client[self.db_name]

            # Force server selection early so invalid URIs/network issues fail during startup.
            await self.client.admin.command("ping")
            
            # Create indexes (don't create index on _id as it's automatically indexed and unique)
            await self.db["subscriptions"].create_index("user_id", unique=True)
            await self.db["plans"].create_index("days", unique=True)
            await self.db["vouchers"].create_index("code", unique=True)
            await self.db["giftcards"].create_index("code", unique=True)
            await self.db["payments"].create_index("user_id")
            
            print("✅ Database connected successfully!")
            return True
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from MongoDB"""
        if self.client:
            self.client.close()
            print("Database disconnected")
    
    # ============ USER MANAGEMENT ============
    
    async def get_or_create_user(self, user_id: int, first_name: str = None, username: str = None) -> dict:
        """Get or create a user"""
        user = await self.db["users"].find_one({"_id": user_id})
        
        if not user:
            user = {
                "_id": user_id,
                "first_name": first_name or f"User {user_id}",
                "username": username,
                "created_at": ist_now(),
                "last_interaction": ist_now(),
            }
            await self.db["users"].insert_one(user)
        else:
            await self.db["users"].update_one(
                {"_id": user_id},
                {"$set": {"last_interaction": ist_now()}}
            )
        
        return user
    
    async def get_user(self, user_id: int) -> Optional[dict]:
        """Get user by ID"""
        return await self.db["users"].find_one({"_id": user_id})
    
    async def get_all_users(self) -> List[dict]:
        """Get all users"""
        cursor = self.db["users"].find()
        return await cursor.to_list(None)
    
    # ============ SUBSCRIPTION MANAGEMENT ============
    
    async def get_subscription(self, user_id: int) -> Optional[dict]:
        """Get user subscription"""
        return await self.db["subscriptions"].find_one({"user_id": user_id})
    
    async def create_subscription(self, user_id: int, days: int, plan_id: str = None) -> dict:
        """Create or update subscription"""
        now = ist_now()
        expiry = now + timedelta(days=days)
        
        subscription = {
            "user_id": user_id,
            "plan_id": plan_id,
            "days": days,
            "created_at": now,
            "expiry_date": expiry,
            "status": "active",
        }
        
        result = await self.db["subscriptions"].update_one(
            {"user_id": user_id},
            {"$set": subscription},
            upsert=True
        )
        
        return subscription
    
    async def extend_subscription(self, user_id: int, days: int) -> Optional[dict]:
        """Extend existing subscription"""
        sub = await self.get_subscription(user_id)
        
        if not sub:
            return await self.create_subscription(user_id, days)
        
        now = ist_now()
        current_expiry = sub.get("expiry_date")
        
        if current_expiry and current_expiry > now:
            new_expiry = current_expiry + timedelta(days=days)
        else:
            new_expiry = now + timedelta(days=days)
        
        await self.db["subscriptions"].update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "expiry_date": new_expiry,
                    "status": "active",
                    "updated_at": now
                }
            }
        )
        
        return await self.get_subscription(user_id)
    
    async def revoke_subscription(self, user_id: int) -> bool:
        """Revoke user subscription"""
        result = await self.db["subscriptions"].delete_one({"user_id": user_id})
        return result.deleted_count > 0
    
    async def check_subscription_valid(self, user_id: int) -> bool:
        """Check if subscription is still valid"""
        sub = await self.get_subscription(user_id)
        
        if not sub:
            return False
        
        expiry = sub.get("expiry_date")
        now = ist_now()
        if expiry and expiry > now:
            return True
        
        return False
    
    async def get_active_subscriptions(self) -> List[dict]:
        """Get all active subscriptions"""
        now = ist_now()
        cursor = self.db["subscriptions"].find({
            "expiry_date": {"$gt": now},
            "status": "active"
        })
        return await cursor.to_list(None)
    
    async def get_expiring_subscriptions(self, hours: int = 24) -> List[dict]:
        """Get subscriptions expiring soon"""
        now = ist_now()
        target_time = now + timedelta(hours=hours)
        
        cursor = self.db["subscriptions"].find({
            "expiry_date": {"$gt": now, "$lte": target_time},
            "status": "active",
            "reminder_sent": {"$ne": True}
        })
        return await cursor.to_list(None)
    
    async def mark_reminder_sent(self, user_id: int):
        """Mark expiry reminder as sent"""
        await self.db["subscriptions"].update_one(
            {"user_id": user_id},
            {"$set": {"reminder_sent": True}}
        )
    
    # ============ SUBSCRIPTION PLANS ============
    
    async def get_plans(self) -> List[dict]:
        """Get all subscription plans"""
        cursor = self.db["plans"].find().sort("days", 1)
        plans = await cursor.to_list(None)
        return [self._convert_objectid(p) for p in plans]
    
    async def add_plan(self, days: int, price: float) -> str:
        """Add new subscription plan"""
        plan = {
            "days": days,
            "price": price,
            "created_at": ist_now()
        }
        result = await self.db["plans"].insert_one(plan)
        return str(result.inserted_id)
    
    async def delete_plan(self, plan_id: str) -> bool:
        """Delete subscription plan"""
        try:
            result = await self.db["plans"].delete_one({"_id": ObjectId(plan_id)})
            return result.deleted_count > 0
        except:
            return False
    
    # ============ VOUCHER CODES ============
    
    async def create_voucher(self, code: str, days: int) -> str:
        """Create new voucher code"""
        voucher = {
            "code": code.upper(),
            "days": days,
            "is_active": True,
            "used_by": None,
            "used_at": None,
            "created_at": ist_now()
        }
        result = await self.db["vouchers"].insert_one(voucher)
        return str(result.inserted_id)
    
    async def get_voucher(self, code: str) -> Optional[dict]:
        """Get voucher by code"""
        return await self.db["vouchers"].find_one({"code": code.upper()})
    
    async def use_voucher(self, code: str, user_id: int) -> bool:
        """Mark voucher as used"""
        result = await self.db["vouchers"].update_one(
            {"code": code.upper(), "is_active": True},
            {
                "$set": {
                    "is_active": False,
                    "used_by": user_id,
                    "used_at": ist_now()
                }
            }
        )
        return result.modified_count > 0
    
    async def get_all_vouchers(self) -> List[dict]:
        """Get all vouchers"""
        cursor = self.db["vouchers"].find()
        return await cursor.to_list(None)
    
    async def delete_voucher(self, code: str) -> bool:
        """Delete voucher code"""
        result = await self.db["vouchers"].delete_one({"code": code.upper()})
        return result.deleted_count > 0
    
    # ============ GIFT CARD CODES ============
    
    async def create_giftcard(self, code: str, amount: float) -> str:
        """Create new gift card code"""
        giftcard = {
            "code": code.upper(),
            "amount": amount,
            "is_active": True,
            "used_by": None,
            "used_at": None,
            "created_at": ist_now()
        }
        result = await self.db["giftcards"].insert_one(giftcard)
        return str(result.inserted_id)
    
    async def get_giftcard(self, code: str) -> Optional[dict]:
        """Get gift card by code"""
        return await self.db["giftcards"].find_one({"code": code.upper()})
    
    async def use_giftcard(self, code: str, user_id: int) -> bool:
        """Mark gift card as used"""
        result = await self.db["giftcards"].update_one(
            {"code": code.upper(), "is_active": True},
            {
                "$set": {
                    "is_active": False,
                    "used_by": user_id,
                    "used_at": ist_now()
                }
            }
        )
        return result.modified_count > 0
    
    async def get_all_giftcards(self) -> List[dict]:
        """Get all gift cards"""
        cursor = self.db["giftcards"].find()
        return await cursor.to_list(None)
    
    async def delete_giftcard(self, code: str) -> bool:
        """Delete gift card code"""
        result = await self.db["giftcards"].delete_one({"code": code.upper()})
        return result.deleted_count > 0
    
    # ============ PAYMENTS ============
    
    async def create_payment_request(self, user_id: int, plan_id: str, amount: float, method: str = "screenshot") -> dict:
        """Create pending payment request"""
        payment = {
            "user_id": user_id,
            "plan_id": plan_id,
            "amount": amount,
            "method": method,  # "screenshot", "voucher", "giftcard"
            "status": "pending",  # pending, approved, rejected
            "created_at": ist_now(),
            "screenshot_file_id": None,
        }
        result = await self.db["payments"].insert_one(payment)
        return {**payment, "_id": str(result.inserted_id)}
    
    async def get_pending_payments(self, user_id: int) -> Optional[dict]:
        """Get pending payment for user"""
        return await self.db["payments"].find_one({"user_id": user_id, "status": "pending"})
    
    async def approve_payment(self, payment_id: str) -> bool:
        """Approve payment"""
        result = await self.db["payments"].update_one(
            {"_id": ObjectId(payment_id)},
            {"$set": {"status": "approved", "approved_at": ist_now()}}
        )
        return result.modified_count > 0
    
    async def reject_payment(self, payment_id: str, reason: str = None) -> bool:
        """Reject payment"""
        update_data = {"status": "rejected", "rejected_at": ist_now()}
        if reason:
            update_data["rejection_reason"] = reason
            
        result = await self.db["payments"].update_one(
            {"_id": ObjectId(payment_id)},
            {"$set": update_data}
        )
        return result.modified_count > 0
    
    # ============ STATISTICS ============
    
    async def get_stats(self) -> dict:
        """Get bot statistics"""
        total_users = await self.db["users"].count_documents({})
        active_subs = len(await self.get_active_subscriptions())
        total_subs = await self.db["subscriptions"].count_documents({})
        
        vouchers = await self.db["vouchers"].find().to_list(None)
        active_vouchers = len([v for v in vouchers if v.get("is_active")])
        used_vouchers = len([v for v in vouchers if not v.get("is_active")])
        
        giftcards = await self.db["giftcards"].find().to_list(None)
        active_giftcards = len([g for g in giftcards if g.get("is_active")])
        used_giftcards = len([g for g in giftcards if not g.get("is_active")])
        
        return {
            "total_users": total_users,
            "active_subscriptions": active_subs,
            "total_subscriptions": total_subs,
            "active_vouchers": active_vouchers,
            "used_vouchers": used_vouchers,
            "active_giftcards": active_giftcards,
            "used_giftcards": used_giftcards,
        }
    
    async def get_expired_subscriptions(self) -> List[dict]:
        """Get all expired subscriptions that haven't been processed"""
        now = ist_now()
        cursor = self.db["subscriptions"].find({
            "expiry_date": {"$lte": now},
            "status": "active",
            "processed": {"$ne": True}
        })
        return await cursor.to_list(None)
    
    async def mark_subscription_processed(self, user_id: int):
        """Mark subscription as processed (user removed from group)"""
        await self.db["subscriptions"].update_one(
            {"user_id": user_id},
            {"$set": {"processed": True, "removed_at": ist_now()}}
        )
    
    async def get_processed_expired_users(self) -> List[dict]:
        """Get expired users for renewal notifications"""
        now = ist_now()
        cursor = self.db["subscriptions"].find({
            "processed": True,
            "removed_at": {"$exists": True},
            "renewal_notified": {"$ne": True}
        })
        return [await self.db["users"].find_one({"_id": sub["user_id"]}) for sub in await cursor.to_list(None)]
    
    async def mark_renewal_notified(self, user_id: int):
        """Mark that renewal notification has been sent"""
        await self.db["subscriptions"].update_one(
            {"user_id": user_id},
            {"$set": {"renewal_notified": True}}
        )
    
    async def mark_user_invalid_payment(self, user_id: int):
        """Mark user as having invalid payment (for automatic removal)"""
        await self.db["users"].update_one(
            {"_id": user_id},
            {"$set": {"invalid_payment": True, "marked_invalid_at": ist_now()}}
        )
    
    async def get_users_with_invalid_payment(self) -> List[dict]:
        """Get users marked with invalid payment for removal"""
        cursor = self.db["users"].find({
            "invalid_payment": True,
            "removed_for_invalid": {"$ne": True}
        })
        return await cursor.to_list(None)
    
    async def mark_user_removed_for_invalid(self, user_id: int):
        """Mark that user has been removed for invalid payment"""
        await self.db["users"].update_one(
            {"_id": user_id},
            {"$set": {"removed_for_invalid": True, "removed_at": ist_now()}}
        )
    
    # ============ HELPER METHODS ============
    
    def _convert_objectid(self, doc: dict) -> dict:
        """Convert ObjectId to string in document"""
        if "_id" in doc and isinstance(doc["_id"], ObjectId):
            doc["_id"] = str(doc["_id"])
        return doc
