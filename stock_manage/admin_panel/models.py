from django.db import models
from django.db.models import Sum
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib.auth.models import User

class AdminProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='admin_profile')
    profile_image = models.ImageField(upload_to='admin/profile/', blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)

    def __str__(self):
        return f"{self.user.username} Profile"

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
    joining_date = models.DateField(blank=True, null=True)
    resignation_date = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)

    def calculate_salary_for_month(self, year, month):
        import calendar
        from datetime import date
        
        month_start = date(year, month, 1)
        _, days_in_month = calendar.monthrange(year, month)
        month_end = date(year, month, days_in_month)

        if self.joining_date and self.joining_date > month_end:
            return None 
        if self.resignation_date and self.resignation_date < month_start:
            return None 

        from .models import Leave
        approved_leaves = Leave.objects.filter(
            worker=self, 
            status='Approved',
            start_date__lte=month_end,
            end_date__gte=month_start
        )
        
        total_leave_days = 0.0
        for l in approved_leaves:
            total_leave_days += l.compute_leave_days(month=month, year=year)

        base_salary = float(self.salary)
        per_day_salary = base_salary / days_in_month
        
        extra_payment = 0.0
        deduction = 0.0
        final_salary = base_salary

        if total_leave_days < 2:
            extra_payment = (2.0 - total_leave_days) * per_day_salary
            final_salary = base_salary + extra_payment
        elif total_leave_days == 2:
            final_salary = base_salary
        else:
            deduction_days = total_leave_days - 2.0
            deduction = deduction_days * per_day_salary
            final_salary = base_salary - deduction

        return {
            'year': year,
            'month': month,
            'month_name': calendar.month_name[month],
            'base_salary': round(base_salary, 2),
            'total_leave_days': total_leave_days,
            'extra_payment': round(extra_payment, 2),
            'deduction': round(deduction, 2),
            'final_salary': round(final_salary, 2),
            'days_in_month': days_in_month,
            'quota_used': min(2.0, total_leave_days)
        }

    def get_salary_history(self):
        from datetime import date
        import calendar
        
        if not self.joining_date:
            return []
            
        start = date(self.joining_date.year, self.joining_date.month, 1)
        end = self.resignation_date or date.today()
        _, d = calendar.monthrange(end.year, end.month)
        end = date(end.year, end.month, d)

        history = []
        curr = start
        while curr <= end:
            res = self.calculate_salary_for_month(curr.year, curr.month)
            if res:
                history.append(res)
            # increment to next month
            if curr.month == 12:
                curr = date(curr.year + 1, 1, 1)
            else:
                curr = date(curr.year, curr.month + 1, 1)
        
        return history[::-1]

    @property
    def name(self):
        return f"{self.first_name} {self.last_name}"

class Category(models.Model):
    name = models.CharField(max_length=100,unique=True)
    status = models.BooleanField(default=True)

    def __str__(self):
        return self.name
    
@receiver(post_save, sender=Category)
def category_post_save(sender, instance, created, **kwargs):
    try:
        layer = get_channel_layer()
        image_url = None
        try:
            p = Product.objects.filter(brand__subcetegory__category=instance, status=True).order_by('-id').first()
            if p and p.image:
                try:
                    image_url = p.image.url
                except Exception:
                    image_url = None
            if not image_url and p:
                pi = ProductImage.objects.filter(product=p).order_by('-id').first()
                if pi and pi.image:
                    try:
                        image_url = pi.image.url
                    except Exception:
                        image_url = None
        except Exception:
            image_url = None
        payload = {"id": instance.id, "name": instance.name, "status": instance.status, "image_url": image_url}
        if created:
            async_to_sync(layer.group_send)("categories", {"type": "category_added", "category": payload})
        else:
            async_to_sync(layer.group_send)("categories", {"type": "category_updated", "category": payload})
    except Exception:
        pass
    
@receiver(post_delete, sender=Category)
def category_post_delete(sender, instance, **kwargs):
    try:
        layer = get_channel_layer()
        async_to_sync(layer.group_send)("categories", {"type": "category_deleted", "id": instance.id})
    except Exception:
        pass
    
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

    @property
    def total_stock(self):
        return self.variants.aggregate(total=Sum('stock'))['total'] or 0

    def __str__(self):
        return self.name
    
class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product.name} image"

 

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
    image = models.ImageField(upload_to='variants/', blank=True, null=True)

    def __str__(self):
        return f"{self.product.name} - {self.color.name} - {self.size.name}"


class VariantImage(models.Model):
    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.CASCADE,
        related_name='gallery_images'
    )
    image = models.ImageField(upload_to='variants/gallery/')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.variant.sku} gallery image"


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
    title = models.CharField(max_length=255, blank=True, null=True)
    image = models.ImageField(upload_to='blogs/', blank=True, null=True)
    des = models.TextField()
    by = models.CharField(max_length=100)
    date = models.DateField()

    def __str__(self):
        return f"{self.title or self.by} - {self.date}"


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
    leave_days = models.FloatField(default=0)  # Total counted as 0, 0.5, 1.0 per day
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at', '-id']

    def __str__(self):
        return f"{self.worker.first_name} {self.worker.last_name} {self.start_date} - {self.end_date} [{self.category}/{self.status}]"

    def _to_date(self, v):
        from datetime import date, datetime
        if isinstance(v, date):
            return v
        if isinstance(v, str) and v:
            try:
                return datetime.strptime(v, "%Y-%m-%d").date()
            except ValueError:
                return None
        return None

    def _to_time(self, v):
        from datetime import time, datetime
        if isinstance(v, time):
            return v
        if isinstance(v, str) and v:
            for fmt in ("%H:%M", "%H:%M:%S"):
                try:
                    return datetime.strptime(v, fmt).time()
                except ValueError:
                    continue
        return None

    def compute_total_minutes(self):
        from datetime import datetime, date, time, timedelta

        s_date = self._to_date(self.start_date)
        e_date = self._to_date(self.end_date)
        s_time_input = self._to_time(self.start_time)
        e_time_input = self._to_time(self.end_time)

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
        self.leave_days = self.compute_leave_days()
        super().save(*args, **kwargs)

    def compute_leave_days(self, month=None, year=None):
        """
        Calculates leave days for this instance. If month/year provided,
        only counts days within that specific month.
        """
        from datetime import datetime, date, time, timedelta
        s_date = self._to_date(self.start_date)
        e_date = self._to_date(self.end_date)
        s_time_input = self._to_time(self.start_time)
        e_time_input = self._to_time(self.end_time)

        if not s_date or not e_date or e_date < s_date:
            return 0
        
        office_start = time(9, 0)
        lunch_start = time(13, 0)
        lunch_end = time(14, 0)
        office_end = time(18, 0)

        def get_day_count(d, s, e):
            s = s or office_start
            e = e or office_end
            s = max(s, office_start)
            e = min(e, office_end)
            if s >= e: return 0
            mins = int((datetime.combine(d, e) - datetime.combine(d, s)).total_seconds() // 60)
            ls = max(s, lunch_start)
            le = min(e, lunch_end)
            if ls < le:
                mins -= int((datetime.combine(d, le) - datetime.combine(d, ls)).total_seconds() // 60)
            mins = max(0, mins)
            
            if mins <= 120: return 0.0
            if mins <= 240: return 0.5
            return 1.0

        total_days = 0.0
        cur = s_date
        while cur <= e_date:
            # If month/year filter is applied
            if month and year:
                if cur.year != year or cur.month != month:
                    cur += timedelta(days=1)
                    continue
            
            s = s_time_input if cur == s_date and s_time_input else office_start
            e = e_time_input if cur == e_date and e_time_input else office_end
            total_days += get_day_count(cur, s, e)
            cur += timedelta(days=1)
        return total_days

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
