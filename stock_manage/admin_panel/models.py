from django.db import models

class Suppliers(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)

    GENDER_CHOICES = [('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')]
    STATUS_CHOICES = [('Active', 'Active'), ('Inactive', 'Inactive')]

    profile_picture = models.ImageField(upload_to='suppliers/profile/', blank=True, null=True)
    document = models.FileField(upload_to='suppliers/documents/', blank=True, null=True)

    password = models.CharField(max_length=10)
    first_name = models.CharField(max_length=20)
    last_name = models.CharField(max_length=20)

    state = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    address = models.CharField(max_length=255, blank=True)

    mbno = models.IntegerField()
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)


class Workers(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)

    GENDER_CHOICES = [('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')]
    STATUS_CHOICES = [('Active', 'Active'), ('Inactive', 'Inactive')]

    profile_picture = models.ImageField(upload_to='worker/profile/', blank=True, null=True)
    document = models.FileField(upload_to='worker/documents/', blank=True, null=True)

    password = models.CharField(max_length=10)
    first_name = models.CharField(max_length=20)
    last_name = models.CharField(max_length=20)

    state = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    address = models.CharField(max_length=255, blank=True)

    mbno = models.IntegerField()
    salary = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)

class Category(models.Model):
    name = models.CharField(max_length=100,unique=True)
    status = models.BooleanField(default=True)

    def __str__(self):
        return self.name
    
class Subcetegory(models.Model):
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name = "subcetegory"
    )
    name = models.CharField(max_length=100)
    status = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.category.name} - {self.name}"
    

class Brand(models.Model):
    subcetegory = models.ForeignKey(
        Subcetegory,
        on_delete=models.CASCADE,
        related_name='brands'
    )
    name = models.CharField(max_length=100)
    status = models.BooleanField(default=True)

    def __str__(self):
        return self.name
    
class Product(models.Model):
    brand = models.ForeignKey(
        Brand,
        on_delete=models.CASCADE,
        related_name='products'
    )
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    base_price = models.DecimalField(max_digits=10,decimal_places=2)
    image  = models.ImageField(upload_to='products/',blank=True,null=True)
    status = models.BooleanField(default=True)

    def __str__(self):
        return self.name
    

class Color(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class Size(models.Model):
    name = models.CharField(max_length=20)  

    def __str__(self):
        return self.name


class ProductVariant(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='variants'
    )
    color = models.ForeignKey(Color, on_delete=models.CASCADE)
    size = models.ForeignKey(Size, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    sku = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return f"{self.product.name} - {self.color.name} - {self.size.name}"


class VariantSpec(models.Model):
    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.CASCADE,
        related_name='specs'
    )
    name = models.CharField(max_length=100)
    value = models.CharField(max_length=255, blank=True)

    class Meta:
        unique_together = ('variant', 'name')

    def __str__(self):
        return f"{self.variant_id} - {self.name}: {self.value}"
    

class Blogs(models.Model):
    image = models.ImageField(upload_to='blogs/', blank=True, null=True)
    des = models.TextField()
    by = models.CharField(max_length=100)
    date = models.DateField()

    def __str__(self):
        return f"{self.by} - {self.date}"


class Contact(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100, blank=True)
    email = models.EmailField()
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        full_name = f"{self.first_name} {self.last_name}".strip()
        return f"{full_name} - {self.email}"


class Holiday(models.Model):
    name = models.CharField(max_length=150)
    date = models.DateField()
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-id']

    def __str__(self):
        return f"{self.name} ({self.date})"
