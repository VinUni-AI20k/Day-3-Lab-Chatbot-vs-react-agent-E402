# Bao cao Trace va Danh gia

## Agentic Fit

| Tieu chi | Diem | Ly do |
|---|---:|---|
| Multi-step reasoning | 5/5 | Doc JD, doc ho so, cham diem va tong hop. |
| Tool interaction | 5/5 | Du lieu job va ung vien nam trong hai CSV rieng. |
| Dynamic decision | 4/5 | Observation loi ID bat buoc doi huong hoac fallback. |
| Long horizon | 3/5 | Flow cham diem can ba Action lien tiep. |
| Tong | 17/20 | Bai toan phu hop voi ReAct Agent. |

## So sanh Test Case 4

Cau hoi: Danh gia muc do phu hop cua ung vien UserID 983877 voi cong viec JobID 0.

### Chatbot Baseline

Chatbot chi tu van chung va tu choi xac nhan JobID, UserID hay diem phu hop
vi khong co tool truy cap CSV.

### ReAct Agent mock

    Thought: Can doc yeu cau cong viec truoc.
    Action: get_job_description[0]
    Observation: JOB [0]: Sale Admin Website ...

    Thought: Can doc ho so ung vien truoc khi cham.
    Action: get_candidate_profile[983877]
    Observation: Da doc ho so UserID 983877 de phuc vu cham diem.

    Thought: Da co JD va ho so, can cham muc phu hop.
    Action: score_candidate[0, 983877]
    Observation: Diem heuristic va cac tieu chi vi tri, ky nang,
    Work Experience, nganh, dia diem.

    Final Answer: HR dung ket qua de xem xet ho so goc.

## Edge Case 5

Voi UserID 99999999, Agent goi get_candidate_profile[99999999], nhan
Observation LOI: Khong tim thay UserID, sau do tra loi an toan. Agent khong
lap lai Action va khong tu tao du lieu ung vien.
