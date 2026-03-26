from django.contrib import admin
from .models import (
    Suppliers, Workers, Category, Subcetegory, Brand, Product, 
    ProductImage, Color, Size, ProductVariant, VariantImage, 
    VariantSpec, Blogs, Contact, Holiday, Leave
)
from buyers.models import (
    Buyer, CartItem, Order, OrderItem, WishlistItem, ProductReview
)

# Register admin_panel models
admin.site.register(Suppliers)
admin.site.register(Workers)
admin.site.register(Category)
admin.site.register(Subcetegory)
admin.site.register(Brand)
admin.site.register(Product)
admin.site.register(ProductImage)
admin.site.register(Color)
admin.site.register(Size)
admin.site.register(ProductVariant)
admin.site.register(VariantImage)
admin.site.register(VariantSpec)
admin.site.register(Blogs)
admin.site.register(Contact)
admin.site.register(Holiday)
admin.site.register(Leave)

# Register buyers models
admin.site.register(Buyer)
admin.site.register(CartItem)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(WishlistItem)
admin.site.register(ProductReview)
