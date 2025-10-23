from django.core.management.base import BaseCommand
from django.core.validators import ValidationError
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Create a staff user with predefined credentials'
    
    """Two ways to run the command
    Example 1: python manage.py staffuser
    Example 2: python manage.py staffuser --email=staff@company.com --phone=+8801712345678 --password=mypassword123
    """

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type    = str,
            help    = 'Email for the staff user',
            default = "staff@test.com"
        )
        parser.add_argument(
            '--phone', 
            type    = str,
            help    = 'Phone number for the staff user',
            default = "+88015000000002"
        )
        parser.add_argument(
            '--password',
            type    = str,
            help    = 'Password for the staff user', 
            default = "123456ra"
        )

    def handle(self, *args, **options):
        email    = options['email']
        phone    = options['phone']
        password = options['password']
        
        # Check if staff user already exists
        if User.objects.filter(email=email).exists():
            self.stdout.write(
                self.style.WARNING(f"Staff user with email {email} already exists.")
            )
            return
        
        if User.objects.filter(phone=phone).exists():
            self.stdout.write(
                self.style.WARNING(f"Staff user with phone {phone} already exists.")
            )
            return

        try:
            # Create staff user - is_staff বাদ দিয়ে শুধু is_admin=True ব্যবহার করুন
            user = User(
                email        = email,
                phone        = phone,
                first_name   = "Mr.",
                last_name    = "Staff",
                is_active    = True,
                is_admin     = True,  # Staff user হিসেবে mark করছি
                is_superuser = False, # Superuser permissions নেই
                is_email_verified = True,
                is_phone_verified = True,
            )
            
            user.set_password(password)
            user.save()
            
            self.stdout.write(
                self.style.SUCCESS(f"Staff user created successfully!")
            )
            self.stdout.write(
                self.style.SUCCESS(f"Email: {email}")
            )
            self.stdout.write(
                self.style.SUCCESS(f"Phone: {phone}")
            )
            self.stdout.write(
                self.style.SUCCESS(f"Password: {password}")
            )
            self.stdout.write(
                self.style.SUCCESS(f"Permissions: Staff Admin (is_admin=True)")
            )
            
        except ValidationError as e:
            self.stdout.write(
                self.style.ERROR(f"Validation Error: {e}")
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Error creating staff user: {e}")
            )