from django import forms
from .models import DailyStock
from apps.partners.models import Partner
from apps.products.models import Product

class DailyStockIntakeForm(forms.ModelForm):
    """
    Form In-Take Barang Masuk Subuh Kasir POS.
    """
    new_product_name = forms.CharField(
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full rounded-xl border border-slate-300 px-3.5 py-2.5 text-sm focus:ring-2 focus:ring-brand-500 focus:border-brand-500',
            'placeholder': 'Ketik nama menu baru jika belum ada di list...',
        })
    )
    new_product_category = forms.ChoiceField(
        choices=Product.CATEGORY_CHOICES,
        required=False,
        initial='snack',
        widget=forms.Select(attrs={
            'class': 'w-full rounded-xl border border-slate-300 px-3.5 py-2.5 text-sm focus:ring-2 focus:ring-brand-500 focus:border-brand-500',
        })
    )

    class Meta:
        model = DailyStock
        fields = ['partner', 'product', 'stock_in', 'proof_photo']
        widgets = {
            'partner': forms.Select(attrs={
                'class': 'w-full rounded-xl border border-slate-300 px-3.5 py-2.5 text-sm focus:ring-2 focus:ring-brand-500 focus:border-brand-500',
                'id': 'select-partner',
                'required': True,
            }),
            'product': forms.Select(attrs={
                'class': 'w-full rounded-xl border border-slate-300 px-3.5 py-2.5 text-sm focus:ring-2 focus:ring-brand-500 focus:border-brand-500',
                'id': 'select-product',
                'required': False,
            }),
            'stock_in': forms.NumberInput(attrs={
                'class': 'w-full text-center font-black text-2xl rounded-xl border border-slate-300 py-3 text-slate-900 focus:ring-2 focus:ring-brand-500 focus:border-brand-500',
                'min': '1',
                'value': '20',
                'required': True,
                'id': 'input-stock-in',
            }),
            'proof_photo': forms.FileInput(attrs={
                'class': 'hidden',
                'id': 'input-proof-photo',
                'accept': 'image/*',
                'capture': 'environment',
            }),
        }

    def __init__(self, *args, branch=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['product'].required = False
        self.fields['partner'].queryset = Partner.objects.filter(is_active=True).order_by('name')
        if branch:
            self.fields['product'].queryset = Product.objects.filter(branch=branch, is_active=True).order_by('name')
        else:
            self.fields['product'].queryset = Product.objects.filter(is_active=True).order_by('name')
