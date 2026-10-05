from django import forms
from .models import Partner

class QuickPartnerForm(forms.ModelForm):
    """
    Form Modal Tambah Mitra Baru On-The-Fly dari Kasir POS.
    """
    class Meta:
        model = Partner
        fields = [
            'name', 'phone_number', 'bank_name',
            'bank_account_name', 'bank_account_number'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full rounded-xl border border-slate-300 px-3.5 py-2.5 text-sm focus:ring-2 focus:ring-brand-500 focus:border-brand-500',
                'placeholder': 'Contoh: Bu Rini Risoles',
                'required': True,
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'w-full rounded-xl border border-slate-300 px-3.5 py-2.5 text-sm focus:ring-2 focus:ring-brand-500 focus:border-brand-500',
                'placeholder': '0812xxxxxxxx',
            }),
            'bank_name': forms.TextInput(attrs={
                'class': 'w-full rounded-xl border border-slate-300 px-3.5 py-2.5 text-sm focus:ring-2 focus:ring-brand-500 focus:border-brand-500',
                'placeholder': 'BCA / BRI / DANA / Mandiri',
            }),
            'bank_account_name': forms.TextInput(attrs={
                'class': 'w-full rounded-xl border border-slate-300 px-3.5 py-2.5 text-sm focus:ring-2 focus:ring-brand-500 focus:border-brand-500',
                'placeholder': 'Nama Pemilik Rekening',
            }),
            'bank_account_number': forms.TextInput(attrs={
                'class': 'w-full rounded-xl border border-slate-300 px-3.5 py-2.5 text-sm focus:ring-2 focus:ring-brand-500 focus:border-brand-500',
                'placeholder': 'No Rekening / No HP E-Wallet',
            }),
        }
