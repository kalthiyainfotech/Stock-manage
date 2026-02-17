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


class Leave(models.Model):
    STATUS_CHOICES = [('Pending', 'Pending'), ('Approved', 'Approved'), ('Rejected', 'Rejected')]
    CATEGORY_CHOICES = [('Sick', 'Sick'), ('Emergency', 'Emergency'), ('Casual', 'Casual')]
    worker = models.ForeignKey(Workers, on_delete=models.CASCADE, related_name='leaves')
    start_date = models.DateField()
    end_date = models.DateField()
    start_time = models.TimeField(blank=True, null=True)
    end_time = models.TimeField(blank=True, null=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='Casual')
    reason = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pending')
    total_minutes = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at', '-id']

    def __str__(self):
        return f"{self.worker.name} {self.start_date} - {self.end_date} [{self.category}/{self.status}]"

    def compute_total_minutes(self):
        from datetime import datetime, date, time, timedelta

        def to_date(v):
            if isinstance(v, date):
                return v
            if isinstance(v, str) and v:
                try:
                    return datetime.strptime(v, "%Y-%m-%d").date()
                except ValueError:
                    return None
            return None

        def to_time(v):
            if isinstance(v, time):
                return v
            if isinstance(v, str) and v:
                for fmt in ("%H:%M", "%H:%M:%S"):
                    try:
                        return datetime.strptime(v, fmt).time()
                    except ValueError:
                        continue
            return None

        s_date = to_date(self.start_date)
        e_date = to_date(self.end_date)
        s_time_input = to_time(self.start_time)
        e_time_input = to_time(self.end_time)

        if not s_date or not e_date:
            return 0
        if e_date < s_date:
            return 0
        office_start = time(9, 0)
        lunch_start = time(13, 0)
        lunch_end = time(14, 0)
        office_end = time(18, 0)

        def day_minutes(d, s, e):
            s = s or office_start
            e = e or office_end
            s = max(s, office_start)
            e = min(e, office_end)
            if s >= e:
                return 0
            total = int((datetime.combine(d, e) - datetime.combine(d, s)).total_seconds() // 60)
            ls = max(s, lunch_start)
            le = min(e, lunch_end)
            if ls < le:
                total -= int((datetime.combine(d, le) - datetime.combine(d, ls)).total_seconds() // 60)
            return max(0, total)

        cur = s_date
        total = 0
        while cur <= e_date:
            if cur == s_date and s_time_input:
                s = s_time_input
            else:
                s = office_start
            if cur == e_date and e_time_input:
                e = e_time_input
            else:
                e = office_end
            total += day_minutes(cur, s, e)
            cur += timedelta(days=1)
        return total

    def save(self, *args, **kwargs):
        self.total_minutes = self.compute_total_minutes()
        super().save(*args, **kwargs)

    @property
    def total_hm(self):
        h = (self.total_minutes or 0) // 60
        m = (self.total_minutes or 0) % 60
        return f"{h}h {m}m"

    @property
    def day_count(self):
        try:
            return (self.end_date - self.start_date).days + 1
        except Exception:
            return 0

    def minutes_in_month(self, year, month):
        from datetime import datetime, date, time, timedelta
        def to_date(v):
            if isinstance(v, date):
                return v
            if isinstance(v, str) and v:
                try:
                    return datetime.strptime(v, "%Y-%m-%d").date()
                except ValueError:
                    return None
            return None
        def to_time(v):
            if isinstance(v, time):
                return v
            if isinstance(v, str) and v:
                for fmt in ("%H:%M", "%H:%M:%S"):
                    try:
                        return datetime.strptime(v, fmt).time()
                    except ValueError:
                        continue
            return None
        s_date = to_date(self.start_date)
        e_date = to_date(self.end_date)
        s_time_input = to_time(self.start_time)
        e_time_input = to_time(self.end_time)
        if not s_date or not e_date:
            return 0
        if e_date < s_date:
            return 0
        office_start = time(9, 0)
        lunch_start = time(13, 0)
        lunch_end = time(14, 0)
        office_end = time(18, 0)
        month_start = date(year, month, 1)
        if month == 12:
            next_month = date(year + 1, 1, 1)
        else:
            next_month = date(year, month + 1, 1)
        month_end = next_month - timedelta(days=1)
        start = s_date if s_date > month_start else month_start
        end = e_date if e_date < month_end else month_end
        if end < start:
            return 0
        def day_minutes(d, s, e):
            s = s or office_start
            e = e or office_end
            s = max(s, office_start)
            e = min(e, office_end)
            if s >= e:
                return 0
            total = int((datetime.combine(d, e) - datetime.combine(d, s)).total_seconds() // 60)
            ls = max(s, lunch_start)
            le = min(e, lunch_end)
            if ls < le:
                total -= int((datetime.combine(d, le) - datetime.combine(d, ls)).total_seconds() // 60)
            return max(0, total)
        cur = start
        total = 0
        while cur <= end:
            if cur == s_date and s_time_input:
                s = s_time_input
            else:
                s = office_start
            if cur == e_date and e_time_input:
                e = e_time_input
            else:
                e = office_end
            total += day_minutes(cur, s, e)
            cur += timedelta(days=1)
        return total
