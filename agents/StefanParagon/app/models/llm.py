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
                                    description="List of purchased products. Must contain at least one product. Don't remove any duplicates.")


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

    response = openai.Client().chat.completions.create(
        model="gpt-4o-2024-08-06",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an intelligent assistant specializing in extracting raw text from receipt images. "
                    "Extract all text exactly as it appears on the receipt, preserving formatting and structure. "
                    "Do not summarize, interpret, or omit any details."
                ),
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "Please analyze the following receipt image and extract all text as-is."
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
        max_tokens=5000,
    )
    receipt_ocr = response.choices[0].message.content

    response = openai.Client().chat.completions.create(
        model="gpt-4o-2024-08-06",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an intelligent assistant that extracts structured information from raw receipt text. "
                    "Extract the following details from the provided text: "
                    "1. All mentioned addresses. "
                    "2. Receipt number or ID. "
                    "3. Taxpayer Identification Number (NIP). "
                    "4. Payment methods used. "
                    "5. Total amount before and after promotions. "
                    "6. General promotions or discounts applied to the total. "
                    "Return the result as plain structured text, preserving clarity and accuracy."
                ),
            },
            {
                "role": "user",
                "content": receipt_ocr,
            },
        ],
        max_tokens=1500,
    )
    receipt_meta = response.choices[0].message.content

    response = openai.Client().chat.completions.create(
        model="gpt-4o-2024-08-06",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an intelligent assistant specializing in extracting structured information from receipt text. "
                    "From the provided receipt, extract a detailed list of all product entries exactly as they appear, including: "
                    "1. Product name. "
                    "2. Unit of measurement (if applicable). "
                    "3. Quantity. "
                    "4. Price per unit. "
                    "5. Total price. "
                    "Do not deduplicate, analyze, or interpret the data. Return the result as a structured plain text list."
                ),
            },
            {
                "role": "user",
                "content": receipt_ocr,
            },
        ],
        max_tokens=1500,
    )
    receipt_products = response.choices[0].message.content

    response = client.chat.completions.create(
        model="gpt-4o-2024-08-06",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an intelligent assistant that extracts structured information from receipt text. "
                    "You specialize in converting raw receipt data into structured JSON, ensuring that all details are preserved. "
                    "Your task is to analyze the provided receipt text and return detailed information in JSON format, based on the user's specific queries."
                ),
            },
            {
                "role": "assistant",
                "content": (
                    "Understood. Please provide the raw text of the receipt, and I will extract the requested structured data."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"The receipt contains the following validated metadata:\n\n{receipt_meta}\n\n"
                    f"And the list of validated products (dont remove any position):\n\n{receipt_products}"
                ),
            },
        ],
        max_tokens=5000,
        response_model=Receipt,
    )

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
