/**
 * Fast In-Take POS Cashier Interface Script
 * Handles dynamic product filtering by partner, on-the-fly partner creation modal,
 * touch stepper controls, and camera snapshot preview.
 */

function initPosIntake() {
    const appContainer = document.getElementById('pos-intake-app');
    const partnerSelect = document.getElementById('select-partner');
    const productSelect = document.getElementById('select-product');
    const branchSlug = appContainer?.dataset?.branchSlug || document.body.dataset.branchSlug || 'ciomas';

    let partnerTom = null;
    let productTom = null;

    // 1. Inisialisasi Tom Select untuk Mitra dan Produk
    if (typeof TomSelect !== 'undefined') {
        if (partnerSelect) {
            if (partnerSelect.tomselect) {
                partnerTom = partnerSelect.tomselect;
            } else {
                try {
                    partnerTom = new TomSelect(partnerSelect, {
                        create: false,
                        allowEmptyOption: true,
                        maxOptions: 300,
                        placeholder: '🔍 Ketik nama mitra atau pilih...',
                        closeAfterSelect: true,
                        render: {
                            no_results: function(data, escape) {
                                return '<div class="no-results">Tidak ada mitra bernama "' + escape(data.input) + '"</div>';
                            },
                            option: function(data, escape) {
                                if (data.value === '') {
                                    return '<div class="option text-slate-400 italic font-normal">-- Pilih Mitra UMKM --</div>';
                                }
                                return '<div class="option font-semibold">' + escape(data.text) + '</div>';
                            },
                            item: function(data, escape) {
                                if (data.value === '') {
                                    return '<span class="text-slate-400 font-normal">-- Pilih Mitra UMKM --</span>';
                                }
                                return '<div>' + escape(data.text) + '</div>';
                            }
                        }
                    });
                    partnerTom.on('item_add', function() {
                        this.blur();
                    });
                    partnerTom.on('change', function() {
                        this.blur();
                    });
                } catch(e) {
                    console.warn('TomSelect partner error:', e);
                }
            }
        }

        if (productSelect) {
            if (productSelect.tomselect) {
                productTom = productSelect.tomselect;
            } else {
                try {
                    productTom = new TomSelect(productSelect, {
                        create: false,
                        allowEmptyOption: true,
                        maxOptions: 300,
                        placeholder: '-- Pilih Menu Masuk --',
                        closeAfterSelect: true,
                        render: {
                            no_results: function(data, escape) {
                                return '<div class="no-results">Tidak ada menu "' + escape(data.input) + '"</div>';
                            },
                            option: function(data, escape) {
                                if (data.value === '') {
                                    return '<div class="option text-slate-400 italic font-normal">-- Pilih Menu Masuk --</div>';
                                }
                                return '<div class="option font-semibold">' + escape(data.text) + '</div>';
                            },
                            item: function(data, escape) {
                                if (data.value === '') {
                                    return '<span class="text-slate-400 font-normal">-- Pilih Menu Masuk --</span>';
                                }
                                return '<div>' + escape(data.text) + '</div>';
                            }
                        }
                    });
                    productTom.on('item_add', function() {
                        this.blur();
                    });
                    productTom.on('change', function() {
                        this.blur();
                    });
                } catch(e) {
                    console.warn('TomSelect product error:', e);
                }
            }
        }
    }

    // 2. Dropdown Dinamis: Saat Mitra Dipilih, Muat Menu Terkait
    function loadProductsForPartner(partnerId) {
        const newMenuContainer = document.getElementById('new-menu-container');

        if (!partnerId) {
            if (productTom) {
                productTom.clear();
                productTom.clearOptions();
                productTom.addOption({ value: '', text: '-- Pilih Mitra Terlebih Dahulu --' });
                productTom.refreshOptions(false);
            } else if (productSelect) {
                productSelect.innerHTML = '<option value="">-- Pilih Mitra Terlebih Dahulu --</option>';
            }
            return;
        }

        if (productTom) {
            productTom.clear();
            productTom.clearOptions();
            productTom.addOption({ value: '', text: '⏳ Memuat daftar menu...' });
            productTom.refreshOptions(false);
        } else if (productSelect) {
            productSelect.innerHTML = '<option value="">⏳ Memuat daftar menu...</option>';
        }

        fetch(`/pos/api/partner/${partnerId}/products/?branch=${branchSlug}`)
            .then(res => res.json())
            .then(data => {
                if (productTom) {
                    productTom.clear();
                    productTom.clearOptions();

                    if (data.products && data.products.length > 0) {
                        data.products.forEach(p => {
                            const icon = p.category === 'makanan_berat' ? '🍱' : (p.category === 'snack' ? '🥐' : '🧃');
                            productTom.addOption({
                                value: String(p.id),
                                text: `${icon} ${p.name} (${p.category})`
                            });
                        });
                        productTom.refreshOptions(false);
                        if (newMenuContainer) newMenuContainer.classList.add('hidden');
                    } else {
                        productTom.addOption({ value: '', text: 'Belum ada menu (Isi menu baru di bawah)' });
                        productTom.refreshOptions(false);
                        if (newMenuContainer) newMenuContainer.classList.remove('hidden');
                    }
                } else if (productSelect) {
                    productSelect.innerHTML = '';
                    if (data.products && data.products.length > 0) {
                        const defaultOpt = document.createElement('option');
                        defaultOpt.value = '';
                        defaultOpt.textContent = '-- Pilih Menu Masuk --';
                        productSelect.appendChild(defaultOpt);

                        data.products.forEach(p => {
                            const opt = document.createElement('option');
                            opt.value = p.id;
                            opt.textContent = `${p.name} (${p.category})`;
                            productSelect.appendChild(opt);
                        });
                        if (newMenuContainer) newMenuContainer.classList.add('hidden');
                    } else {
                        const opt = document.createElement('option');
                        opt.value = '';
                        opt.textContent = 'Belum ada menu (Isi menu baru di bawah)';
                        productSelect.appendChild(opt);
                        if (newMenuContainer) newMenuContainer.classList.remove('hidden');
                    }
                }
            })
            .catch(err => {
                console.error('Error fetching partner products:', err);
                if (productTom) {
                    productTom.clear();
                    productTom.clearOptions();
                    productTom.addOption({ value: '', text: 'Gagal memuat menu' });
                    productTom.refreshOptions(false);
                } else if (productSelect) {
                    productSelect.innerHTML = '<option value="">Gagal memuat menu</option>';
                }
            });
    }

    if (partnerTom) {
        partnerTom.on('change', function(value) {
            loadProductsForPartner(value);
        });
        // Jika sudah ada mitra yang terpilih saat load
        if (partnerTom.getValue()) {
            loadProductsForPartner(partnerTom.getValue());
        }
    } else if (partnerSelect) {
        partnerSelect.addEventListener('change', function () {
            loadProductsForPartner(this.value);
        });
        if (partnerSelect.value) {
            loadProductsForPartner(partnerSelect.value);
        }
    }

    // Toggle Input Menu Baru
    const toggleNewMenuBtn = document.getElementById('btn-toggle-new-menu');
    const newMenuContainer = document.getElementById('new-menu-container');
    if (toggleNewMenuBtn && newMenuContainer) {
        toggleNewMenuBtn.addEventListener('click', function () {
            newMenuContainer.classList.toggle('hidden');
            if (!newMenuContainer.classList.contains('hidden')) {
                const newMenuInput = document.getElementById('id_new_product_name');
                if (newMenuInput) newMenuInput.focus();
            }
        });
    }

    // 3. Tombol Stepper Kuantitas (+5, +10, -5, -1)
    const stockInput = document.getElementById('input-stock-in');
    const stepperBtns = document.querySelectorAll('.stepper-btn');

    stepperBtns.forEach(btn => {
        btn.addEventListener('click', function () {
            if (!stockInput) return;
            const delta = parseInt(this.dataset.step || '0');
            let currentVal = parseInt(stockInput.value || '0');
            let newVal = Math.max(1, currentVal + delta);
            stockInput.value = newVal;
        });
    });

    // 4. Preview Foto Bukti Serah Terima Fisik
    const photoInput = document.getElementById('input-proof-photo');
    const photoPreviewContainer = document.getElementById('photo-preview-container');
    const photoPreviewImg = document.getElementById('photo-preview-img');
    const photoUploadLabel = document.getElementById('photo-upload-label');

    if (photoInput) {
        photoInput.addEventListener('change', function () {
            if (this.files && this.files[0]) {
                const file = this.files[0];
                const reader = new FileReader();

                reader.onload = function (e) {
                    if (photoPreviewImg) photoPreviewImg.src = e.target.result;
                    if (photoPreviewContainer) photoPreviewContainer.classList.remove('hidden');
                    if (photoUploadLabel) {
                        photoUploadLabel.innerHTML = `
                            <span class="text-emerald-700 font-bold flex items-center gap-1.5">
                                <svg class="w-4 h-4 text-emerald-600 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                                </svg>
                                Foto Berhasil Dipilih (${(file.size / 1024).toFixed(0)} KB)
                            </span>
                        `;
                    }
                };

                reader.readAsDataURL(file);
            }
        });
    }

    // 5. Modal Tambah Mitra Baru On-The-Fly (AJAX)
    const openModalBtn = document.getElementById('btn-open-modal-mitra');
    const closeModalBtn = document.getElementById('btn-close-modal-mitra');
    const modal = document.getElementById('modal-tambah-mitra');
    const quickPartnerForm = document.getElementById('form-quick-partner');

    if (openModalBtn && modal) {
        openModalBtn.addEventListener('click', () => modal.classList.remove('hidden'));
    }

    if (closeModalBtn && modal) {
        closeModalBtn.addEventListener('click', () => modal.classList.add('hidden'));
    }

    if (modal) {
        // Klik di luar area modal untuk menutup
        modal.addEventListener('click', function (e) {
            if (e.target === modal) modal.classList.add('hidden');
        });
    }

    if (quickPartnerForm) {
        quickPartnerForm.addEventListener('submit', function (e) {
            e.preventDefault();

            const submitBtn = this.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.textContent = 'Menyimpan Mitra...';
            }

            const formData = new FormData(this);

            fetch('/mitra/api/quick-create/', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(res => res.json())
            .then(data => {
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.textContent = 'Simpan & Pilih Mitra';
                }

                if (data.status === 'success') {
                    // Tambahkan opsi mitra baru ke dropdown
                    if (partnerTom) {
                        partnerTom.addOption({ value: data.partner.id, text: data.partner.name });
                        partnerTom.setValue(data.partner.id);
                    } else if (partnerSelect) {
                        const newOpt = document.createElement('option');
                        newOpt.value = data.partner.id;
                        newOpt.textContent = data.partner.name;
                        newOpt.selected = true;
                        partnerSelect.appendChild(newOpt);
                        partnerSelect.value = data.partner.id;
                        partnerSelect.dispatchEvent(new Event('change'));
                    }

                    // Tutup modal dan reset form
                    if (modal) modal.classList.add('hidden');
                    quickPartnerForm.reset();

                    alert(`Sukses! Mitra "${data.partner.name}" berhasil ditambahkan dan otomatis dipilih.`);
                } else {
                    const errMsg = data.errors ? Object.values(data.errors).join('\n') : 'Terjadi kesalahan validasi.';
                    alert('Gagal: ' + errMsg);
                }
            })
            .catch(err => {
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.textContent = 'Simpan & Pilih Mitra';
                }
                console.error('Error creating partner:', err);
                alert('Terjadi kesalahan koneksi server.');
            });
        });
    }
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initPosIntake);
} else {
    initPosIntake();
}
