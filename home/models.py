from django.db import models


class Category(models.Model):



    Title = models.CharField(max_length = 250)
    Slug = models.SlugField(unique = True , max_length = 250)
    Created_date = models.DateTimeField(auto_now_add = True)
    Updated_date = models.DateTimeField(auto_now = True)

    
    def __str__(self):

        return f'{self.id} , {self.Title}'
    
class Product(models.Model):

    Category = models.ForeignKey("Category" , null = True ,  blank = True , on_delete = models.SET_NULL)
    Name = models.CharField(max_length = 250)
    Content = models.TextField()
    Image = models.ImageField(upload_to = 'blog/' , null = True , blank = True)
    Available = models.BooleanField(default=True)
    Price = models.IntegerField()
    Stock = models.PositiveIntegerField()
    Created_at = models.DateTimeField(auto_now_add=True)
    Updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):

        return str(self.ProductName) - str(self.Status) - str(self.Price)




class Comment(models.Model):
    Products = models.ForeignKey(Product,on_delete=models.CASCADE,related_name='comments')
    name = models.CharField(max_length=80)
    email = models.EmailField()
    body = models.TextField()
    created_on = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=False)
    class Meta:
        ordering = ['created_on']

    def __str__(self):
        return 'Comment {} by {}'.format(self.body, self.name)