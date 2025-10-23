from django.core.management.base import BaseCommand
from django.core.validators import ValidationError
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Create a superuser with predefined credentials'

    def handle(self, *args, **options):
        email    = "admin@test.com"
        phone    = "+88015000000001"
        password = "123456ra"
        
        # Check if superuser already exists
        if User.objects.filter(email=email).exists():
            self.stdout.write(
                self.style.WARNING(f"Superuser with email {email} already exists.")
            )
            return
        
        if User.objects.filter(phone=phone).exists():
            self.stdout.write(
                self.style.WARNING(f"Superuser with phone {phone} already exists.")
            )
            return

        try:
            # Create superuser manually
            user = User(
                email        = email,
                phone        = phone,
                first_name   = "Mr. Supper",
                last_name    = "Admin",
                is_active    = True,
                is_admin     = True,   # Django admin (is_staff) access  
                is_superuser = True,   # Superuser permissions
                is_email_verified = True,
                is_phone_verified = True,
            )
            
            user.set_password(password)
            user.save()
            
            self.stdout.write(
                self.style.SUCCESS(f"Superuser created successfully!")
            )
            self.stdout.write(
                self.style.SUCCESS(f"Email: {email}")
            )
            self.stdout.write(
                self.style.SUCCESS(f"Phone: {phone}")
            )
            
        except ValidationError as e:
            self.stdout.write(
                self.style.ERROR(f"Validation Error: {e}")
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Error creating superuser: {e}")
            )