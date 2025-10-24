# Slug Generation Utilities

## Overview

The `dtpyfw.core.slug` module provides helpers for normalizing strings into URL-friendly slugs. Slugs are used in URLs, file names, and identifiers where you need clean, readable, and URL-safe strings.

## Module Path

```python
from dtpyfw.core.slug import create_slug
```

## Functions

### `create_slug(name: str) -> str | None`

Generate a URL-friendly slug from a string.

**Description:**

Converts a string into a slug by lowercasing it, replacing spaces with hyphens, removing special characters, and normalizing diacritics (accented characters). The result is a clean, URL-safe string suitable for use in URLs, file names, or identifiers.

**Parameters:**

- **name** (`str`): The string to convert into a slug

**Returns:**

- **`str`**: The generated slug, or
- **`None`**: If the input is empty or results in an empty slug

**Transformation Rules:**

1. Convert to lowercase
2. Replace spaces with hyphens
3. Remove characters that aren't letters, numbers, hyphens, or underscores
4. Normalize Unicode characters (remove diacritics)
5. Remove leading and trailing hyphens

**Example:**

```python
from dtpyfw.core.slug import create_slug

# Basic example
slug = create_slug("Hello World")
print(slug)  # Output: hello-world

# With special characters
slug = create_slug("Product #123 (New!)")
print(slug)  # Output: product-123-new

# With accented characters
slug = create_slug("Café München")
print(slug)  # Output: cafe-munchen

# With multiple spaces
slug = create_slug("Multiple   Spaces")
print(slug)  # Output: multiple---spaces

# Empty input
slug = create_slug("")
print(slug)  # Output: None
```

## Complete Usage Examples

### 1. Blog Post URLs

```python
from dtpyfw.core.slug import create_slug
from datetime import datetime

class BlogPost:
    def __init__(self, title: str, content: str):
        self.title = title
        self.content = content
        self.slug = create_slug(title)
        self.created_at = datetime.now()
    
    def get_url(self) -> str:
        """Generate URL for blog post."""
        date_str = self.created_at.strftime("%Y/%m/%d")
        return f"/blog/{date_str}/{self.slug}"

# Usage
post = BlogPost("How to Use Python Effectively", "Content here...")
print(post.get_url())
# Output: /blog/2024/10/15/how-to-use-python-effectively
```

### 2. Product Catalog

```python
from dtpyfw.core.slug import create_slug

class Product:
    def __init__(self, name: str, sku: str, price: float):
        self.name = name
        self.sku = sku
        self.price = price
        self.slug = create_slug(name)
    
    def get_product_url(self) -> str:
        """Generate SEO-friendly product URL."""
        return f"/products/{self.slug}-{self.sku.lower()}"
    
    def get_image_filename(self) -> str:
        """Generate image filename."""
        return f"{self.slug}-main.jpg"

# Usage
product = Product("Sony WH-1000XM5 Headphones", "SN-WH1000XM5", 399.99)
print(product.get_product_url())
# Output: /products/sony-wh-1000xm5-headphones-sn-wh1000xm5

print(product.get_image_filename())
# Output: sony-wh-1000xm5-headphones-main.jpg
```

### 3. File Upload Handler

```python
from dtpyfw.core.slug import create_slug
import os
from uuid import uuid4

class FileUploader:
    def __init__(self, upload_dir: str = "/uploads"):
        self.upload_dir = upload_dir
    
    def generate_filename(self, original_filename: str) -> str:
        """Generate clean, unique filename."""
        # Split name and extension
        name, ext = os.path.splitext(original_filename)
        
        # Create slug from name
        slug = create_slug(name)
        
        # Add unique identifier
        unique_id = str(uuid4())[:8]
        
        return f"{slug}-{unique_id}{ext.lower()}"
    
    def get_file_path(self, original_filename: str) -> str:
        """Get full file path."""
        filename = self.generate_filename(original_filename)
        return os.path.join(self.upload_dir, filename)

# Usage
uploader = FileUploader()
filepath = uploader.get_file_path("My Document (Final) v2.pdf")
print(filepath)
# Output: /uploads/my-document-final-v2-a1b2c3d4.pdf
```

### 4. User Profile URLs

```python
from dtpyfw.core.slug import create_slug

class UserProfile:
    def __init__(self, username: str, full_name: str):
        self.username = username
        self.full_name = full_name
        self.slug = create_slug(full_name) or create_slug(username)
    
    def get_profile_url(self) -> str:
        """Generate user profile URL."""
        return f"/users/{self.slug}"
    
    def get_vanity_url(self) -> str:
        """Generate short vanity URL."""
        return f"/@{self.slug}"

# Usage
user = UserProfile("john_doe", "John Doe Jr.")
print(user.get_profile_url())  # /users/john-doe-jr
print(user.get_vanity_url())   # /@john-doe-jr
```

### 5. SEO-Friendly URLs

```python
from dtpyfw.core.slug import create_slug
from fastapi import FastAPI

app = FastAPI()

class Article:
    def __init__(self, id: int, title: str):
        self.id = id
        self.title = title
        self.slug = create_slug(title)
    
    def get_canonical_url(self) -> str:
        """Get canonical URL for SEO."""
        return f"https://example.com/articles/{self.id}/{self.slug}"

@app.get("/articles/{article_id}/{slug}")
def get_article(article_id: int, slug: str):
    """Get article by ID and slug."""
    article = fetch_article(article_id)
    
    # Redirect if slug doesn't match (SEO best practice)
    if create_slug(article.title) != slug:
        return RedirectResponse(
            url=f"/articles/{article_id}/{article.slug}",
            status_code=301
        )
    
    return article

# Usage
article = Article(123, "10 Tips for Better Python Code")
print(article.get_canonical_url())
# https://example.com/articles/123/10-tips-for-better-python-code
```

### 6. Category and Tag Management

```python
from dtpyfw.core.slug import create_slug

class Category:
    def __init__(self, name: str, parent: 'Category' = None):
        self.name = name
        self.slug = create_slug(name)
        self.parent = parent
    
    def get_full_slug(self) -> str:
        """Get hierarchical slug."""
        if self.parent:
            return f"{self.parent.get_full_slug()}/{self.slug}"
        return self.slug
    
    def get_url(self) -> str:
        """Get category URL."""
        return f"/categories/{self.get_full_slug()}"

# Usage
electronics = Category("Electronics & Gadgets")
computers = Category("Computers & Laptops", parent=electronics)
gaming = Category("Gaming Laptops", parent=computers)

print(gaming.get_url())
# Output: /categories/electronics--gadgets/computers--laptops/gaming-laptops
```

### 7. API Endpoint Generator

```python
from dtpyfw.core.slug import create_slug

class APIEndpoint:
    def __init__(self, resource_name: str):
        self.resource_name = resource_name
        self.slug = create_slug(resource_name)
    
    def get_list_endpoint(self) -> str:
        """Get list endpoint."""
        return f"/api/v1/{self.slug}"
    
    def get_detail_endpoint(self, resource_id: int) -> str:
        """Get detail endpoint."""
        return f"/api/v1/{self.slug}/{resource_id}"
    
    def get_action_endpoint(self, resource_id: int, action: str) -> str:
        """Get action endpoint."""
        action_slug = create_slug(action)
        return f"/api/v1/{self.slug}/{resource_id}/{action_slug}"

# Usage
endpoint = APIEndpoint("User Profiles")
print(endpoint.get_list_endpoint())
# Output: /api/v1/user-profiles

print(endpoint.get_detail_endpoint(123))
# Output: /api/v1/user-profiles/123

print(endpoint.get_action_endpoint(123, "Reset Password"))
# Output: /api/v1/user-profiles/123/reset-password
```

### 8. Database-Backed Slug with Uniqueness

```python
from dtpyfw.core.slug import create_slug
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Page(Base):
    __tablename__ = 'pages'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(200))
    slug = Column(String(200), unique=True)
    
    def __init__(self, title: str, db_session):
        self.title = title
        self.slug = self._generate_unique_slug(title, db_session)
    
    def _generate_unique_slug(self, title: str, db_session) -> str:
        """Generate unique slug by appending number if needed."""
        base_slug = create_slug(title)
        slug = base_slug
        counter = 1
        
        while db_session.query(Page).filter_by(slug=slug).first():
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        return slug

# Usage
page1 = Page("About Us", db_session)  # slug: about-us
page2 = Page("About Us", db_session)  # slug: about-us-1
page3 = Page("About Us", db_session)  # slug: about-us-2
```

## Edge Cases and Special Characters

```python
from dtpyfw.core.slug import create_slug

# Numbers
print(create_slug("Product 123"))  # product-123

# Underscores (preserved)
print(create_slug("my_variable_name"))  # my_variable_name

# Hyphens (preserved)
print(create_slug("pre-release"))  # pre-release

# Mixed case
print(create_slug("iPhone 15 Pro"))  # iphone-15-pro

# Special characters (removed)
print(create_slug("Price: $99.99!"))  # price-9999

# Leading/trailing spaces and hyphens
print(create_slug("  --test--  "))  # test

# Unicode normalization
print(create_slug("Björk"))  # bjork
print(create_slug("naïve"))  # naive
print(create_slug("façade"))  # facade

# Chinese/Japanese characters (removed if not in ASCII)
print(create_slug("你好世界"))  # empty → None

# Emoji (removed)
print(create_slug("Hello 👋 World"))  # hello--world
```

## Best Practices

1. **Always check for None:**
   ```python
   slug = create_slug(user_input)
   if slug is None:
       slug = "untitled"
   ```

2. **Store slugs in database:**
   ```python
   class Article:
       title = Column(String)
       slug = Column(String, unique=True, index=True)
   ```

3. **Use for URLs, not display:**
   ```python
   # Good
   url = f"/products/{product.slug}"
   
   # Don't do this
   print(f"Product: {product.slug}")  # Use product.name instead
   ```

4. **Validate slug length:**
   ```python
   slug = create_slug(title)
   if slug and len(slug) > 100:
       slug = slug[:100].rstrip('-')
   ```

5. **Handle duplicates:**
   ```python
   def ensure_unique_slug(base_slug, existing_slugs):
       slug = base_slug
       counter = 1
       while slug in existing_slugs:
           slug = f"{base_slug}-{counter}"
           counter += 1
       return slug
   ```

## Common Patterns

### URL Generation Helper

```python
from dtpyfw.core.slug import create_slug

def create_seo_url(base_path: str, title: str, id: int = None) -> str:
    """Create SEO-friendly URL with optional ID."""
    slug = create_slug(title) or "untitled"
    if id:
        return f"/{base_path}/{id}/{slug}"
    return f"/{base_path}/{slug}"
```

### Filename Sanitizer

```python
from dtpyfw.core.slug import create_slug
import os

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for filesystem."""
    name, ext = os.path.splitext(filename)
    slug = create_slug(name) or "file"
    return f"{slug}{ext.lower()}"
```

## Related Modules

- **dtpyfw.core.validation** - Input validation
- **dtpyfw.db.model** - Database models with slug fields
- **dtpyfw.api.routes** - API routing with slugs

## Dependencies

- `re` - Regular expressions
- `unicodedata` - Unicode normalization

## See Also

- [URL Slugs Best Practices](https://developers.google.com/search/docs/crawling-indexing/url-structure)
- [Unicode Normalization](https://docs.python.org/3/library/unicodedata.html)
- [Django's slugify](https://docs.djangoproject.com/en/stable/ref/utils/#django.utils.text.slugify)
