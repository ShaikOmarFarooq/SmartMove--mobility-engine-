import uuid
import random
from domain.user import User


class UserFactory:
    FIRST_NAMES = [
        "Alex", "Maria", "Luca", "Emma", "Noah",
        "Sophia", "James", "Elena", "Daniel", "Sara"
    ]

    @staticmethod
    def create_user() -> User:
        user_id = f"U-{uuid.uuid4()}"
        name = random.choice(UserFactory.FIRST_NAMES)

        return User(user_id=user_id, name=name)

    @staticmethod
    def create_users(count: int) -> dict:
        users = {}

        for _ in range(count):
            user = UserFactory.create_user()
            users[user.id] = user

        return users
