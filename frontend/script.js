
const API_URL = "http://127.0.0.1:8000";

const $ = (id) => document.getElementById(id);

let allStudents = [];
let toastTimer;

function showToast(message) {
    const toast = $("toast");
    if (!toast) return;

    toast.textContent = message;
    toast.classList.add("show");

    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => toast.classList.remove("show"), 3000);
}

function escapeHTML(value) {
    return String(value ?? "").replace(/[&<>"']/g, char => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;"
    })[char]);
}

function todayString() {
    const now = new Date();

    return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-${String(now.getDate()).padStart(2, "0")}`;
}

function formatDate(date) {
    return date.toLocaleDateString("en-IN", {
        day: "numeric",
        month: "short",
        year: "numeric"
    });
}

// Initial dates
$("today-date").textContent = formatDate(new Date());
$("attendance-date").value = todayString();


// API request helper
async function apiRequest(path, options = {}) {
    const response = await fetch(`${API_URL}${path}`, {
        ...options,
        headers: {
            "Content-Type": "application/json",
            ...(options.headers || {})
        }
    });

    if (!response.ok) {
        let message = `Request failed (${response.status})`;

        try {
            const errorData = await response.json();
            message = errorData.detail || message;
        } catch {
            // Keep default error message
        }

        throw new Error(message);
    }

    if (response.status === 204) return null;

    const responseText = await response.text();

    return responseText ? JSON.parse(responseText) : null;
}


// Dashboard navigation
function showPage(page) {
    document.querySelectorAll(".page").forEach(section => {
        section.classList.add("hidden");
    });

    const selectedPage = $(`${page}-page`);

    if (!selectedPage) return;

    selectedPage.classList.remove("hidden");

    document.querySelectorAll(".nav-link").forEach(link => {
        link.classList.toggle("active", link.dataset.page === page);
    });

    const titles = {
        dashboard: "Dashboard",
        students: "Students",
        attendance: "Attendance Records"
    };

    $("page-title").textContent = titles[page] || "Dashboard";

    if (page === "students") loadStudents();
    if (page === "attendance") loadAttendance();
}

document.querySelectorAll(".nav-link").forEach(link => {
    link.addEventListener("click", event => {
        event.preventDefault();
        showPage(link.dataset.page);
    });
});

document.querySelectorAll("[data-go]").forEach(button => {
    button.addEventListener("click", () => showPage(button.dataset.go));
});

$("view-students-btn").addEventListener("click", () => {
    showPage("students");
});


// Student management
async function loadStudents() {
    $("students-table").innerHTML =
        '<tr><td colspan="5" class="empty">Loading students...</td></tr>';

    try {
        const result = await apiRequest("/students");

        allStudents = Array.isArray(result)
            ? result
            : (result.students || []);

        renderStudents();
        updateDashboardStats();

    } catch (error) {
        console.error(error);

        $("students-table").innerHTML =
            '<tr><td colspan="5" class="empty">Could not load students. Check backend.</td></tr>';

        showToast("Cannot connect to backend.");
    }
}

function renderStudents() {
    const search = $("student-search").value.trim().toLowerCase();

    const filtered = allStudents.filter(student =>
        [student.name, student.roll_no, student.course, student.id]
            .some(value => String(value ?? "").toLowerCase().includes(search))
    );

    if (filtered.length === 0) {
        $("students-table").innerHTML =
            '<tr><td colspan="5" class="empty">No students found.</td></tr>';
        return;
    }

    $("students-table").innerHTML = filtered.map(student => `
        <tr>
            <td>#${escapeHTML(student.id)}</td>
            <td><strong>${escapeHTML(student.name)}</strong></td>
            <td>${escapeHTML(student.roll_no)}</td>
            <td>
                <span class="course-badge">
                    ${escapeHTML(student.course)}
                </span>
            </td>
            <td>
                <button class="table-action edit-student"
                    data-id="${escapeHTML(student.id)}"
                    title="Edit student">
                    <i class="fa-solid fa-pen"></i>
                </button>

                <button class="table-action delete delete-student"
                    data-id="${escapeHTML(student.id)}"
                    title="Delete student">
                    <i class="fa-solid fa-trash"></i>
                </button>
            </td>
        </tr>
    `).join("");
}

$("student-search").addEventListener("input", renderStudents);

$("students-table").addEventListener("click", event => {
    const editButton = event.target.closest(".edit-student");
    const deleteButton = event.target.closest(".delete-student");

    if (editButton) {
        const student = allStudents.find(item =>
            String(item.id) === editButton.dataset.id
        );

        if (student) openEditForm(student);
    }

    if (deleteButton) {
        deleteStudent(deleteButton.dataset.id);
    }
});


// Add student form
function openAddForm() {
    $("student-form").reset();
    $("student-id").value = "";

    $("student-form-title").textContent = "Add New Student";
    $("student-form-card").classList.remove("hidden");

    $("student-name").focus();
}

function openEditForm(student) {
    $("student-id").value = student.id;
    $("student-name").value = student.name || "";
    $("student-roll").value = student.roll_no || "";
    $("student-course").value = student.course || "";

    $("student-form-title").textContent = "Edit Student";
    $("student-form-card").classList.remove("hidden");

    $("student-form-card").scrollIntoView({
        behavior: "smooth"
    });
}

$("show-add-form").addEventListener("click", openAddForm);

$("cancel-form").addEventListener("click", () => {
    $("student-form-card").classList.add("hidden");
    $("student-form").reset();
});


// Save student and start face registration
$("student-form").addEventListener("submit", async event => {
    event.preventDefault();

    const id = $("student-id").value;

    const student = {
        name: $("student-name").value.trim(),
        roll_no: $("student-roll").value.trim(),
        course: $("student-course").value.trim()
    };

    if (!student.name || !student.roll_no || !student.course) {
        showToast("Please fill in all fields.");
        return;
    }

    const submitButton = $("student-form").querySelector(
        'button[type="submit"]'
    );

    submitButton.disabled = true;

    try {
        if (id) {
            // Update existing student
            await apiRequest(`/students/${id}`, {
                method: "PUT",
                body: JSON.stringify(student)
            });

            showToast("Student updated successfully!");

        } else {
            // Add new student
            const result = await apiRequest("/students", {
                method: "POST",
                body: JSON.stringify(student)
            });

            const newStudentId = result.student_id;

            $("student-form-card").classList.add("hidden");
            $("student-form").reset();

            await loadStudents();

            // Automatically start face registration
            try {
                await apiRequest(
                    `/students/${newStudentId}/register-face`,
                    {
                        method: "POST"
                    }
                );

                showToast(
                    "Student added! Face registration camera started."
                );

            } catch (cameraError) {
                console.error(cameraError);

                showToast(
                    "Student saved, but face registration could not start: " +
                    cameraError.message
                );
            }

            return;
        }

        $("student-form-card").classList.add("hidden");
        $("student-form").reset();

        await loadStudents();

    } catch (error) {
        console.error(error);
        showToast(error.message || "Could not save student.");

    } finally {
        submitButton.disabled = false;
    }
});


// Delete student
async function deleteStudent(id) {
    const student = allStudents.find(item =>
        String(item.id) === String(id)
    );

    if (!student) return;

    if (!confirm(`Delete ${student.name}? This action may affect related records.`)) {
        return;
    }

    try {
        await apiRequest(`/students/${id}`, {
            method: "DELETE"
        });

        await loadStudents();

        showToast("Student deleted successfully.");

    } catch (error) {
        console.error(error);
        showToast(error.message || "Could not delete student.");
    }
}


// Dashboard statistics
async function updateDashboardStats() {
    $("total-students").textContent = allStudents.length;

    try {
        const summary = await apiRequest(
            `/attendance/summary?selected_date=${todayString()}`
        );

        $("present-today").textContent = summary.present;
        $("attendance-rate").textContent =
            `${summary.attendance_percentage}%`;

        // Update absent count if this element exists in HTML
        if ($("absent-today")) {
            $("absent-today").textContent = summary.absent;
        }

    } catch (error) {
        console.error(error);

        $("present-today").textContent = "—";
        $("attendance-rate").textContent = "—";

        if ($("absent-today")) {
            $("absent-today").textContent = "—";
        }
    }
}


// Attendance history and daily summary
async function loadAttendance() {
    $("attendance-table").innerHTML =
        '<tr><td colspan="5" class="empty">Loading attendance...</td></tr>';

    try {
        const selectedDate = $("attendance-date").value;

        // Get all recorded attendance entries
        const records = await apiRequest(
            selectedDate
                ? `/attendance?selected_date=${selectedDate}`
                : "/attendance"
        );

        const attendance = Array.isArray(records)
            ? records
            : (records.attendance || []);

        // Get daily summary, including absent students
        if (selectedDate) {
            const summary = await apiRequest(
                `/attendance/summary?selected_date=${selectedDate}`
            );

            $("attendance-total").textContent = summary.present;

            if ($("attendance-absent")) {
                $("attendance-absent").textContent = summary.absent;
            }

            if ($("attendance-percentage")) {
                $("attendance-percentage").textContent =
                    `${summary.attendance_percentage}%`;
            }

            // Display all students, including absent
            const students = summary.students || [];

            if (students.length === 0) {
                $("attendance-table").innerHTML =
                    '<tr><td colspan="5" class="empty">No students registered.</td></tr>';
                return;
            }

            $("attendance-table").innerHTML = students.map(student => `
                <tr>
                    <td><strong>${escapeHTML(student.name)}</strong></td>
                    <td>${escapeHTML(student.roll_no)}</td>
                    <td>${escapeHTML(summary.date)}</td>
                    <td>${escapeHTML(student.attendance_time || "—")}</td>
                    <td>
                        <span class="${student.status === "Present" ? "present-badge" : "absent-badge"}">
                            ${escapeHTML(student.status)}
                        </span>
                    </td>
                </tr>
            `).join("");

        } else {
            // All recorded historical attendance
            $("attendance-total").textContent = attendance.length;

            if (!attendance.length) {
                $("attendance-table").innerHTML =
                    '<tr><td colspan="5" class="empty">No attendance records found.</td></tr>';
                return;
            }

            $("attendance-table").innerHTML = attendance.map(record => `
                <tr>
                    <td><strong>${escapeHTML(record.student_name || "Unknown")}</strong></td>
                    <td>${escapeHTML(record.roll_no || "—")}</td>
                    <td>${escapeHTML(record.attendance_date || "—")}</td>
                    <td>${escapeHTML(record.attendance_time || "—")}</td>
                    <td>
                        <span class="present-badge">
                            ${escapeHTML(record.status || "Present")}
                        </span>
                    </td>
                </tr>
            `).join("");
        }

    } catch (error) {
        console.error(error);

        $("attendance-total").textContent = "—";

        $("attendance-table").innerHTML =
            '<tr><td colspan="5" class="empty">Could not load attendance. Check backend.</td></tr>';
    }
}

$("refresh-attendance").addEventListener("click", loadAttendance);

$("attendance-date").addEventListener("change", loadAttendance);


// Initial dashboard
showPage("dashboard");
loadStudents();
