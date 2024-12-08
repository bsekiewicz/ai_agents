import base64
import os
from typing import List, Optional, Literal

import instructor
import openai
from pydantic import BaseModel, Field

# Load the OpenAI API key from environment variables
openai.api_key = os.getenv("OPENAI_API_KEY")


class Address(BaseModel):
    """
    Represents the address associated with the store
    """
    city: str = Field(..., description="City")
    state_or_region: str = Field(..., description="State or region")
    street: str = Field(..., description="Street name and number")
    postal_code: str = Field(..., pattern=r"^\d{2}-\d{3}$", description="Postal code in the format XX-XXX")


class Store(BaseModel):
    """
    Represents information about the store where the purchase was made
    """
    name: str = Field(..., description="Store name")
    addresses: List[Address] = Field(..., min_items=1,
                                     description="List of addresses related to the store")
    tax_id: Optional[str] = Field(None, description="Store's tax identification number (if available)")

    def get_purchase_address(self) -> Address:
        """
        Returns the purchase address from the list of addresses.
        If there are multiple addresses, returns the second one. Otherwise, returns the first.
        """
        return self.addresses[1] if len(self.addresses) > 1 else self.addresses[0]


class ProductCategory(BaseModel):
    """
    Represents the product category in a hierarchical structure
    """
    general_category: str = Field(...,
                                  description="Top-level product category, e.g., 'Groceries', 'Chemicals', 'Electronics'")
    sub_category: str = Field(...,
                              description="Subcategory within the general category, e.g., 'Dairy', 'Snacks', 'Sweets'")
    product_type: str = Field(..., description="Detailed product type, e.g., 'Milk', 'Butter', 'Chocolate'")


class Product(BaseModel):
    """
    Information about the purchased product
    """
    name: str = Field(..., description="Product name")
    category: ProductCategory = Field(..., description="Product category")
    promotional: bool = Field(False, description="Indicates if the product is under promotion")
    quantity: float = Field(1.0, gt=0,
                            description="Quantity of units (e.g., pieces, kilograms). Must be greater than zero")
    unit_of_measure: str = Field("pcs", description="Unit of measure (e.g., pcs, kg, l)")
    unit_price: Optional[float] = Field(None, gt=0,
                                        description="Price per unit before discount. Must be greater than zero if provided")
    total_price: float = Field(..., gt=0,
                               description="Total price before discount. Must be greater than zero")
    discount: Optional[float] = Field(0.0, ge=0, description="Discount amount per unit. Defaults to 0")
    total_price_with_discount: float = Field(..., gt=0,
                                             description="Total price after discount. Must be greater than zero")


class ReceiptDiscount(BaseModel):
    """
    General discounts on the receipt (optional)
    """
    description: str = Field(..., description="Description of the discount (e.g., 'Loyalty discount')")
    amount: float = Field(..., gt=0,
                          description="Discount amount in the specified currency. Must be greater than zero")


class Receipt(BaseModel):
    """
    Represents complete receipt information, including store details, products, and discounts
    """
    receipt_number: str = Field(..., description="Fiscal receipt number")
    store: Store = Field(..., description="Information about the store where the purchase was made")
    date: str = Field(..., description="Date the receipt was issued (format YYYY-MM-DD)")
    time: str = Field(..., description="Time the receipt was issued (format HH:MM:SS)")
    payment_method: Literal["card", "cash", "transfer", "blik"] = \
        Field(..., description="Payment method (e.g., card, cash, transfer, blik)")
    currency: Literal["PLN", "EUR", "USD"] = Field("PLN",
                                                   description="Currency of the product price (e.g., PLN, EUR, USD)")
    total_amount: float = Field(..., gt=0,
                                description="Total amount payable on the receipt. Must be greater than zero")
    total_discount: Optional[float] = Field(0.0, ge=0,
                                            description="Total discount amount on the receipt. Defaults to 0")
    discounts: List[ReceiptDiscount] = Field(default_factory=list,
                                             description="List of general discounts on the receipt (can be empty)")
    products: List[Product] = Field(..., min_items=1,
                                    description="List of purchased products. Must contain at least one product")


def encode_image(file_path: str) -> str:
    """
    Encodes an image file to Base64 format.

    Args:
        file_path (str): Path to the image file.

    Returns:
        str: Base64-encoded string of the image.
    """
    with open(file_path, "rb") as image_file:
        base64_image = base64.b64encode(image_file.read()).decode("utf-8")
    return base64_image


def analyze_receipt(file_path: str) -> Receipt:
    """
    Simulates the analysis of a receipt. This is a dummy case for now.

    Args:
        file_path (str): Path to the receipt image file.

    Returns:
        ReceiptAnalysisResult: Simulated analysis data.
    """
    client = instructor.patch(openai.OpenAI(), mode=instructor.Mode.MD_JSON)

    base64_image = encode_image(file_path)

    response = client.chat.completions.create(
        model="gpt-4o-2024-08-06",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an intelligent and highly capable assistant specializing in extracting detailed information "
                    "from receipt images. Your primary task is to analyze receipts accurately and provide structured data "
                    "in strict JSON format based on the content of the image."
                    "Rules for analysis:"
                    "1. Validate the number of unique items extracted against the receipt. Ensure the total matches the number of listed entries."
                    "2. Include all items from the receipt, even if they appear multiple times. Do not group identical items; each instance should be listed separately as it appears on the receipt."
                    "3. Cross-check the total amount and itemized prices, ensuring that the calculated total matches the receipt's total."
                ),
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "Please analyze the following receipt image and extract all relevant data. Respond strictly in the JSON format as described in the schema."
                        ),
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        },
                    },
                ],
            },
        ],
        response_model=Receipt,
        max_tokens=5000,
    )

    total_amount_test = sum([product.total_price for product in response.products]) - response.total_amount
    print(total_amount_test)
    if abs(total_amount_test) > 0.001:
        print(
            f"Warning: Total amount calculated does not match the receipt's total. Total amount difference: {total_amount_test:.2f}")
        response = client.chat.completions.create(
            model="gpt-4o-2024-08-06",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an intelligent and highly capable assistant specializing in extracting detailed information "
                        "from receipt images. Your primary task is to analyze receipts accurately and provide structured data "
                        "in strict JSON format based on the content of the image."
                        "Rules for analysis:"
                        "1. Validate the number of unique items extracted against the receipt. Ensure the total matches the number of listed entries."
                        "2. Include all items from the receipt, even if they appear multiple times. Do not group identical items; each instance should be listed separately as it appears on the receipt."
                        "3. Cross-check the total amount and itemized prices, ensuring that the calculated total matches the receipt's total."
                    ),
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "Please analyze the following receipt image and extract all relevant data. Respond strictly in the JSON format as described in the schema."
                            ),
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            },
                        },
                    ],
                },
                {
                    "role": "assistant",
                    "content": response.model_dump_json()
                },
                {
                    "role": "user",
                    "content": (
                        f"The calculated sum of the itemized prices differs from the total amount on the receipt by {total_amount_test}. "
                        "This discrepancy suggests that one or more items may have been missed or incorrectly scanned. "
                        "Please carefully review the image again and ensure that all items are listed completely and accurately"
                    ),
                }
            ],
            response_model=Receipt,
            max_tokens=5000,
        )
    total_amount_test = sum([product.total_price for product in response.products]) - response.total_amount
    if abs(total_amount_test) > 0.001:
        print(
            f"Warning: Total amount calculated does not match the receipt's total. Total amount difference: {total_amount_test:.2f}")
        response = analyze_receipt_dummy()

    print(response)

    return response


def analyze_receipt_dummy() -> Receipt:
    """
    Simulates the analysis of a receipt. This is a dummy case for now.

    Returns:
        ReceiptAnalysisResult: Simulated analysis data.
    """
    return Receipt(
        receipt_number="XXX",
        store=Store(
            name="Dummy",
            addresses=[
                Address(
                    city="Dummy",
                    state_or_region="Dummy",
                    street="Dummy",
                    postal_code="00-000"
                )
            ],
            tax_id="Dummy"
        ),
        date="1900-01-01",
        time="08:08",
        payment_method="card",
        currency="PLN",
        total_amount=1.0,
        total_discount=0.0,
        discounts=[],
        products=[
            Product(
                name="Smth wrg",
                category=ProductCategory(
                    general_category="Error",
                    sub_category="Error",
                    product_type="Error"
                ),
                promotional=False,
                quantity=1,
                unit_of_measure="pcs",
                unit_price=1.0,
                total_price=1.0,
                discount=0.0,
                total_price_with_discount=1.0
            )
        ]
    )
