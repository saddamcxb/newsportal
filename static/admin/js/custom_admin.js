// অ্যাডমিন প্যানেলের জন্য কাস্টম জাভাস্ক্রিপ্ট
document.addEventListener('DOMContentLoaded', function() {
    
    // কনফার্মেশন ডায়ালগ কাস্টমাইজ
    const deleteButtons = document.querySelectorAll('.deletelink');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (!confirm('আপনি কি নিশ্চিত যে আপনি এই আইটেমটি মুছতে চান?')) {
                e.preventDefault();
            }
        });
    });
    
    // ব্যাচ অ্যাকশন কনফার্মেশন
    const actionForm = document.querySelector('#changelist-form');
    if (actionForm) {
        actionForm.addEventListener('submit', function(e) {
            const selectedAction = document.querySelector('#action-toggle, .action-select');
            if (selectedAction && selectedAction.value === 'delete_selected') {
                if (!confirm('আপনি কি নির্বাচিত আইটেমগুলি মুছতে চান?')) {
                    e.preventDefault();
                }
            }
        });
    }
    
    // ড্যাশবোর্ডে পরিসংখ্যান দেখান
    if (window.location.pathname === '/admin/') {
        addDashboardStats();
    }
    
    function addDashboardStats() {
        // এখানে ড্যাশবোর্ডে কাস্টম স্ট্যাটিস্টিকস যোগ করা যায়
        console.log('অ্যাডমিন ড্যাশবোর্ড লোড হয়েছে');
    }
    
    // স্লাগ অটো-জেনারেট ফাংশন
    const titleInput = document.querySelector('#id_title');
    const slugInput = document.querySelector('#id_slug');
    
    if (titleInput && slugInput) {
        titleInput.addEventListener('blur', function() {
            if (!slugInput.value) {
                let slug = this.value
                    .toLowerCase()
                    .replace(/[^\w\s-]/g, '')
                    .replace(/\s+/g, '-')
                    .replace(/--+/g, '-')
                    .trim();
                slugInput.value = slug;
            }
        });
    }
    
    // ইমেজ প্রিভিউ ফাংশন
    const imageInput = document.querySelector('#id_image');
    if (imageInput) {
        imageInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    // ইমেজ প্রিভিউ দেখানোর জন্য
                    const previewDiv = document.querySelector('.image-preview');
                    if (previewDiv) {
                        previewDiv.innerHTML = `<img src="${e.target.result}" style="max-width: 200px; margin-top: 10px;">`;
                    }
                };
                reader.readAsDataURL(file);
            }
        });
    }
});