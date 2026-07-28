# Tool Specifications: Tro ly tuyen dung CSV

Nguon du lieu:

- data/JOB_DATA_FINAL.csv: viec lam, dinh danh bang JobID.
- data/USER_DATA_FINAL.csv: ung vien, dinh danh bang UserID.

Tat ca tool la read-only. Agent khong dat lich, gui email, cap nhat trang thai,
hoac tu dong dua ra quyet dinh tuyen dung.

| Tool | Input | Muc dich |
|---|---|---|
| search_jobs | keyword, location, limit | Tim job theo tu khoa va dia diem. |
| list_jobs | limit | Liet ke toi da 10 job de LLM co the doc. |
| get_job_description | job_id | Lay JD chi tiet theo JobID. |
| search_candidates | keyword, location, limit | Tim ung vien theo ky nang, vi tri hoac dia diem. |
| get_candidate_profile | user_id | Lay ho so theo UserID. |
| get_resume_content | user_id | Alias cua get_candidate_profile. |
| score_candidate | job_id, user_id | Cham diem ho tro HR. |

## Du lieu va loi

- JobID va UserID la ID thuc trong CSV, vi du 0 va 976112.
- Ket qua tim kiem gioi han 1-10 dong de tranh day prompt.
- Tim kiem khong phan biet hoa thuong va dau tieng Viet.
- ID khong ton tai tra ve chuoi bat dau bang LOI:. Agent phai doc loi,
  khong duoc lap lai cung Action.

## Cham diem ung vien

score_candidate[job_id, user_id] tra ve diem heuristic tren 100:

| Tieu chi | Toi da | Nguon du lieu |
|---|---:|---|
| Tuong dong vi tri | 15 | Job Title va Desired Job |
| Ky nang/nhiem vu | 40 | Job Requirements, Job Description, Skills, Target |
| Work Experience | 30 | Years of Experience va Work Experience |
| Nganh | 10 | Industry |
| Dia diem | 5 | Job Address va Workplace Desired |

Diem ky nang khong dem thuan so tu trung. Tool bo tu pho bien, chi dung truong
Skills cua ung vien va gan trong so cao hon cho tu xuat hien it trong tap JD.
Vi vay cac tu chung nhu giao, hoc hoac phong khong the day diem ky nang len muc
toi da.

Work Experience duoc quy doi theo can duoi: 1-3 nam -> 1, 3-5 nam -> 3,
5-10 nam -> 5, Tren 10 nam -> 10. Neu job khong yeu cau kinh nghiem,
ung vien dat du 30 diem cua tieu chi nay.

Ket qua >= 60 chi la Uu tien HR xem xet. HR phai kiem tra JD va ho so goc
truoc moi quyet dinh. Tool khong su dung tuoi, gioi tinh, hon nhan hay
bat ky thuoc tinh nhay cam nao de cham diem.

## Trace ReAct mau

    Thought: Can doc yeu cau cong viec truoc.
    Action: get_job_description[0]
    Observation: JOB [0]: Sale Admin Website ...

    Thought: Can doc ho so ung vien truoc khi cham.
    Action: get_candidate_profile[976112]
    Observation: UNG VIEN [976112]: nguyen Ba Nghi ...

    Thought: Da co JD va ho so, can cham muc phu hop.
    Action: score_candidate[0, 976112]
    Observation: DANH GIA HO TRO HR: ...

    Final Answer: HR su dung ket qua de xem xet ho so goc.
