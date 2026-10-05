from datetime import date, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from apps.branches.models import Branch
from .models import Partner, DailyAttendance
from .forms import QuickPartnerForm


@staff_member_required(login_url='admin:login')
def attendance_h1_view(request):
    """
    Modul Operator-Assisted Absensi H-1.
    Admin/operator menginput kesiapan antar mitra untuk jadwal besok pagi
    berdasarkan chat WhatsApp mitra.
    """
    branches = Branch.objects.filter(is_active=True).order_by('name')
    selected_slug = request.GET.get('branch', 'ciomas')
    selected_branch = branches.filter(slug=selected_slug).first()
    if not selected_branch and branches.exists():
        selected_branch = branches.first()

    # Default tanggal target: Besok (H-1)
    target_date_str = request.GET.get('date')
    if target_date_str:
        try:
            target_date = date.fromisoformat(target_date_str)
        except ValueError:
            target_date = date.today() + timedelta(days=1)
    else:
        target_date = date.today() + timedelta(days=1)

    today = date.today()

    if request.method == 'POST':
        # Batch save attendance form
        partner_ids = request.POST.getlist('partner_id')
        updated_count = 0

        for pid in partner_ids:
            status = request.POST.get(f'status_{pid}')
            notes = request.POST.get(f'notes_{pid}', '').strip()

            partner = Partner.objects.filter(id=pid).first()
            if partner:
                if status in ('hadir', 'libur'):
                    DailyAttendance.objects.update_or_create(
                        date=target_date,
                        partner=partner,
                        branch=selected_branch,
                        defaults={
                            'status': status,
                            'notes': notes,
                        }
                    )
                    updated_count += 1
                elif notes:
                    # Bila ada catatan khusus, simpan otomatis
                    DailyAttendance.objects.update_or_create(
                        date=target_date,
                        partner=partner,
                        branch=selected_branch,
                        defaults={
                            'status': 'hadir',
                            'notes': notes,
                        }
                    )
                    updated_count += 1

        messages.success(
            request,
            f"Rekap absensi ({updated_count} mitra terisi) untuk jadwal {target_date.strftime('%d %B %Y')} berhasil disimpan."
        )
        return redirect(f"{request.path}?branch={selected_branch.slug}&date={target_date.isoformat()}")

    # Ambil seluruh mitra aktif
    partners = Partner.objects.filter(is_active=True).order_by('name')

    # Ambil record absensi yang sudah tercatat untuk tanggal & cabang ini
    attendances_map = {
        att.partner_id: att
        for att in DailyAttendance.objects.filter(branch=selected_branch, date=target_date)
    }

    # Susun list partner beserta status absensinya
    partner_attendances = []
    hadir_count = 0
    libur_count = 0
    belum_absen_count = 0

    for p in partners:
        att = attendances_map.get(p.id)
        if att:
            current_status = att.status
            current_time = att.estimated_arrival_time
            current_notes = att.notes
            if current_status == 'hadir':
                hadir_count += 1
            else:
                libur_count += 1
        else:
            current_status = 'belum'
            current_time = '05:30:00'
            current_notes = ''
            belum_absen_count += 1

        partner_attendances.append({
            'partner': p,
            'status': current_status,
            'time': current_time,
            'notes': current_notes,
            'attendance_id': att.id if att else None,
        })

    context = {
        'branches': branches,
        'selected_branch': selected_branch,
        'target_date': target_date,
        'today': today,
        'tomorrow': today + timedelta(days=1),
        'partner_attendances': partner_attendances,
        'hadir_count': hadir_count,
        'libur_count': libur_count,
        'belum_absen_count': belum_absen_count,
        'total_partners': len(partners),
    }
    return render(request, 'partners/attendance.html', context)


@require_POST
def api_toggle_attendance(request):
    """
    Endpoint AJAX untuk toggle status absensi instan (1 klik) tanpa refresh.
    Mendukung pemilik/operator mencicil input absensi sepanjang hari H-1.
    """
    partner_id = request.POST.get('partner_id')
    branch_id = request.POST.get('branch_id')
    date_str = request.POST.get('date')
    status = request.POST.get('status')
    notes = request.POST.get('notes', '')

    if not partner_id or not branch_id or not date_str:
        return JsonResponse({'status': 'error', 'message': 'Data tidak lengkap'}, status=400)

    try:
        att_date = date.fromisoformat(date_str)
        partner = Partner.objects.get(id=partner_id)
        branch = Branch.objects.get(id=branch_id)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    if status in ('belum', 'reset'):
        DailyAttendance.objects.filter(date=att_date, partner=partner, branch=branch).delete()
        new_status = 'belum'
        msg = f"Absensi {partner.name} direset (Belum Konfirmasi)"
    elif status in ('hadir', 'libur'):
        att, _ = DailyAttendance.objects.update_or_create(
            date=att_date,
            partner=partner,
            branch=branch,
            defaults={
                'status': status,
                'notes': notes,
            }
        )
        new_status = att.status
        msg = f"Absensi {partner.name} diset [{status.upper()}]"
    else:
        # Hanya perbarui catatan
        att = DailyAttendance.objects.filter(date=att_date, partner=partner, branch=branch).first()
        if att:
            att.notes = notes
            att.save(update_fields=['notes'])
            new_status = att.status
        else:
            new_status = 'belum'
        msg = f"Catatan {partner.name} tersimpan"

    # Hitung live counters terbaru
    total_partners = Partner.objects.filter(is_active=True).count()
    hadir_count = DailyAttendance.objects.filter(branch=branch, date=att_date, status='hadir').count()
    libur_count = DailyAttendance.objects.filter(branch=branch, date=att_date, status='libur').count()
    belum_absen_count = max(0, total_partners - (hadir_count + libur_count))

    return JsonResponse({
        'status': 'success',
        'message': msg,
        'partner_id': partner.id,
        'new_status': new_status,
        'counts': {
            'total': total_partners,
            'hadir': hadir_count,
            'libur': libur_count,
            'belum': belum_absen_count,
        }
    })


@require_POST
def api_create_partner_quick(request):
    """
    Endpoint AJAX untuk membuat mitra baru on-the-fly dari modal kasir POS.
    """
    form = QuickPartnerForm(request.POST)
    if form.is_valid():
        partner = form.save()
        return JsonResponse({
            'status': 'success',
            'message': f"Mitra [{partner.name}] berhasil didaftarkan!",
            'partner': {
                'id': partner.id,
                'name': partner.name,
                'phone': partner.phone_number,
                'bank': partner.bank_name,
            }
        })
    else:
        errors = {field: errs[0] for field, errs in form.errors.items()}
        return JsonResponse({
            'status': 'error',
            'errors': errors
        }, status=400)
