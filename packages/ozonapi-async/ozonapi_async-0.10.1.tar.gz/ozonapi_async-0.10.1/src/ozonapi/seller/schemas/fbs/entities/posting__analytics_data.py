import datetime
from typing import Optional

from pydantic import Field, BaseModel

from ....common.enumerations.postings import PaymentTypeGroupName


class PostingFBSAnalyticsData(BaseModel):
    """Данные аналитики.

    Attributes:
        city: Город доставки
        delivery_date_begin: Дата и время начала доставки
        delivery_date_end: Дата и время конца доставки
        delivery_type: Способ доставки
        is_legal: Признак юридического лица
        is_premium: Наличие подписки Premium
        payment_type_group_name: Способ оплаты
        region: Регион доставки
        tpl_provider: Служба доставки
        tpl_provider_id: Идентификатор службы доставки
        warehouse: Название склада отправки заказа
        warehouse_id: Идентификатор склада
    """
    city: Optional[str] = Field(
        ..., description="Город доставки. Только для отправлений rFBS и продавцов из СНГ."
    )
    delivery_date_begin: Optional[datetime.datetime] = Field(
        None, description="Дата и время начала доставки."
    )
    delivery_date_end: Optional[datetime.datetime] = Field(
        None, description="Дата и время конца доставки."
    )
    delivery_type: str = Field(
        None, description="Способ доставки."
    )
    is_legal: bool = Field(
        ..., description="Признак, что получатель юридическое лицо."
    )
    is_premium: bool = Field(
        ..., description="Наличие подписки Premium."
    )
    payment_type_group_name: PaymentTypeGroupName | str = Field(
        ..., description="Способ оплаты."
    )
    region: Optional[str] = Field(
        ..., description="Регион доставки. Только для отправлений rFBS."
    )
    tpl_provider: str = Field(
        ..., description="Служба доставки."
    )
    tpl_provider_id: int = Field(
        ..., description="Идентификатор службы доставки."
    )
    warehouse: str = Field(
        ..., description="Название склада отправки заказа."
    )
    warehouse_id: int = Field(
        ..., description="Идентификатор склада."
    )
