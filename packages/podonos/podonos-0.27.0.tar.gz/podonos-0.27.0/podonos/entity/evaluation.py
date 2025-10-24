from dataclasses import dataclass
from typing import Optional, Any, Dict
from datetime import datetime


@dataclass
class EvaluationEntity:
    id: str
    title: str
    internal_name: Optional[str]
    description: Optional[str]
    batch_size: int
    status: str
    created_time: datetime
    updated_time: datetime

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "EvaluationEntity":
        required_keys = ["id", "title", "batch_size", "status", "created_time", "updated_time"]
        for key in required_keys:
            if key not in data:
                raise ValueError(f"Invalid data format for Evaluation: {data}")

        return EvaluationEntity(
            id=data["id"],
            title=data["title"],
            internal_name=data["internal_name"],
            description=data["description"],
            batch_size=data["batch_size"],
            status=data["status"],
            created_time=datetime.fromisoformat(data["created_time"].replace("Z", "+00:00")),
            updated_time=datetime.fromisoformat(data["updated_time"].replace("Z", "+00:00")),
        )

    def to_dict(self) -> Dict[str, Any]:
        created_time_str = self.created_time.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        updated_time_str = self.updated_time.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        return {
            "id": self.id,
            "title": self.title,
            "internal_name": self.internal_name,
            "description": self.description,
            "batch_size": self.batch_size,
            "status": self.status,
            "created_time": created_time_str,
            "updated_time": updated_time_str,
        }
