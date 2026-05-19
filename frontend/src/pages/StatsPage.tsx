import { useQuery } from "@tanstack/react-query";
import { Bar, BarChart, CartesianGrid, Cell, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api } from "../api/client";

const scamTypeLabels: Record<string, string> = {
  bank_transfer: "Chuyển khoản rồi biến mất",
  fake_seller: "Bán hàng giả / không giao hàng",
  fake_job: "Việc làm giả, thu phí trước",
  investment: "Đầu tư lợi nhuận cao bất thường",
  impersonation: "Giả danh người quen / cơ quan",
  call_low: "Cuộc gọi đáng ngờ – Rủi ro thấp",
  call_medium: "Cuộc gọi đáng ngờ – Trung bình",
  call_high: "Cuộc gọi lừa đảo – Nguy hiểm cao",
  call_critical: "Cuộc gọi lừa đảo – Cực kỳ nguy hiểm",
  "Thong bao trung thuong yeu cau dong phi": "Thông báo trúng thưởng, yêu cầu đóng phí",
  "Gia danh ngan hang xin ma OTP": "Giả danh ngân hàng xin mã OTP",
  "Gia danh cong an doa lien quan vu an": "Giả danh công an, dọa liên quan vụ án",
  "Moi dau tu loi cao": "Mời đầu tư lợi nhuận cao",
  other: "Hình thức khác",
};

// Short one-line description for each scam type shown in the legend table
const scamTypeDesc: Record<string, string> = {
  call_critical: "Giả danh công an / tòa án, ép chuyển tiền hoặc đọc OTP ngay",
  call_high: "Giả danh ngân hàng, thông báo trúng thưởng + đóng phí, dụ đầu tư",
  call_medium: "Số lạ, kịch bản chưa rõ, nghi ngờ cần theo dõi thêm",
  call_low: "Quảng cáo, gọi nhầm hoặc khảo sát, rủi ro thấp",
  bank_transfer: "Nhận tiền chuyển khoản rồi biến mất, không giao hàng / dịch vụ",
  fake_seller: "Bán hàng giả, lấy cọc trước rồi không giao hoặc giao hàng kém chất lượng",
  fake_job: "Tuyển dụng giả, yêu cầu đóng phí hoặc mua thiết bị trước khi làm việc",
  investment: "Hứa lợi nhuận cao chắc chắn, dụ nạp thêm tiền mới được rút",
  impersonation: "Giả danh người thân, cơ quan nhà nước để xin tiền hoặc thông tin",
  "Giả danh công an, dọa liên quan vụ án": "Dọa liên quan vụ án, yêu cầu xử lý tài chính khẩn cấp",
  "Thông báo trúng thưởng, yêu cầu đóng phí": "Báo trúng thưởng rồi yêu cầu đóng phí, thuế, lệ phí",
  "Giả danh ngân hàng xin mã OTP": "Giả nhân viên ngân hàng để xin mã OTP chiếm đoạt tài khoản",
  other: "",
};

const warningPatterns = [
  {
    title: "Hối chuyển tiền ngay",
    signs: ["Nói đang rất gấp", "Dọa khóa tài khoản hoặc mất cơ hội", "Không cho bạn thời gian hỏi người thân"],
    advice: "Dừng lại 10 phút. Gọi cho người thân hoặc ngân hàng bằng số chính thức trước khi chuyển tiền.",
  },
  {
    title: "Giả danh công an, ngân hàng, shipper",
    signs: ["Yêu cầu đọc mã OTP", "Gửi link lạ để đăng nhập", "Nói bạn liên quan đến vụ án hoặc đơn hàng"],
    advice: "Không đọc mã OTP cho bất kỳ ai. Cơ quan thật không yêu cầu chuyển tiền qua điện thoại.",
  },
  {
    title: "Bán hàng giá rẻ bất thường",
    signs: ["Giá rẻ hơn thị trường quá nhiều", "Bắt cọc trước", "Không cho kiểm tra hàng hoặc địa chỉ rõ ràng"],
    advice: "Ưu tiên thanh toán khi nhận hàng. Kiểm tra số điện thoại hoặc tài khoản trước khi cọc.",
  },
  {
    title: "Đầu tư lời cao, hoàn tiền nhanh",
    signs: ["Hứa chắc chắn có lời", "Ban đầu cho rút ít tiền để tạo lòng tin", "Sau đó bắt nạp thêm mới rút được"],
    advice: "Không tin lời hứa lợi nhuận chắc chắn. Hỏi người có kinh nghiệm tài chính trước khi nạp tiền.",
  },
];

type TrendChartItem = {
  date: string;
  date_label: string;
  reports: number;
  new_entities: number;
  "báo cáo lừa đảo": number;
  "đối tượng mới": number;
};

type ByTypeItem = {
  scam_type: string;
  count: number;
  scam_type_label: string;
  color: string;
};

export function StatsPage() {
  const overview = useQuery({
    queryKey: ["stats-overview"],
    queryFn: async () => (await api.get("/stats/overview")).data,
  });
  const byType = useQuery({
    queryKey: ["stats-type"],
    queryFn: async () => (await api.get("/stats/by-type")).data,
  });
  const trend = useQuery({
    queryKey: ["stats-trend"],
    queryFn: async () => (await api.get("/stats/trend", { params: { range: "30d" } })).data,
  });

  const cards = [
    ["Tổng cảnh báo", overview.data?.total_reports ?? 0],
    ["Cảnh báo cần chú ý", overview.data?.approved_reports ?? 0],
    ["Số điện thoại / mẫu lừa đảo đã biết", overview.data?.total_scam_entities ?? 0],
    ["Rủi ro cao", overview.data?.high_risk_entities ?? 0],
    ["Cảnh báo 7 ngày qua", overview.data?.reports_last_7_days ?? 0],
  ];

  const pieColors = ["#dc2626", "#f59e0b", "#16a34a", "#2563eb", "#8b5cf6", "#ec4899", "#0f766e", "#c026d3", "#475569"];

  const getPieColor = (scamType: string, index: number) => {
    const mappingIndex = Object.keys(scamTypeLabels).indexOf(scamType);
    return pieColors[mappingIndex >= 0 ? mappingIndex % pieColors.length : index % pieColors.length];
  };

  const byTypeData: ByTypeItem[] = (byType.data?.items ?? []).map((item: { scam_type: string; count: number }, index: number) => ({
    ...item,
    scam_type_label: scamTypeLabels[item.scam_type] ?? item.scam_type,
    color: getPieColor(item.scam_type, index),
  }));

  const totalByType = byTypeData.reduce((s, it) => s + (it.count ?? 0), 0);
  const byTypeWithPercent = byTypeData.map((it) => ({
    ...it,
    percent: totalByType ? Math.round((it.count / totalByType) * 100) : 0,
  }));

  // Show items with count >= 2 individually; group count=1 items into "Hình thức khác"
  const sorted = [...byTypeWithPercent].sort((a, b) => (b.count ?? 0) - (a.count ?? 0));
  const top = sorted.filter((it) => (it.count ?? 0) >= 2);
  const others = sorted.filter((it) => (it.count ?? 0) > 0 && (it.count ?? 0) < 2);
  const othersCount = others.reduce((s, it) => s + (it.count ?? 0), 0);
  const pieSlices = [...top];
  if (othersCount > 0) {
    pieSlices.push({
      scam_type: "other",
      scam_type_label: scamTypeLabels["other"],
      count: othersCount,
      color: getPieColor("other", top.length),
      percent: totalByType ? Math.round((othersCount / totalByType) * 100) : 0,
    });
  }

  const trendData: TrendChartItem[] = (trend.data?.items ?? []).map((item: { date: string; reports: number; new_entities: number }) => ({
    ...item,
    date_label: formatShortDate(item.date),
    "báo cáo lừa đảo": item.reports,
    "đối tượng mới": item.new_entities,
  }));
  const trendTotal = trendData.reduce((sum, item) => sum + item.reports, 0);
  const peakDay = trendData.reduce((peak, item) => (item.reports > peak.reports ? item : peak), {
    date: "",
    date_label: "Chưa có",
    reports: 0,
    new_entities: 0,
    "báo cáo lừa đảo": 0,
    "đối tượng mới": 0,
  });
  const activeTrendDays = trendData
    .filter((item) => item.reports > 0)
    .slice(-8)
    .reverse();

  return (
    <section className="stats-page">
      <div className="metric-grid stats-metrics">
        {cards.map(([label, value]) => (
          <div className="panel metric-card" key={label}>
            <span>{label}</span>
            <strong>{value}</strong>
          </div>
        ))}
      </div>
      <div className="chart-grid">
        <div className="panel chart-panel">
          <h2>Cảnh báo theo hình thức</h2>
          <ResponsiveContainer width="100%" height={320}>
            <PieChart>
              <Tooltip formatter={(value: number, name: string) => [value, name]} />
              <Pie
                data={pieSlices}
                dataKey="count"
                nameKey="scam_type_label"
                cx="50%"
                cy="45%"
                innerRadius={70}
                outerRadius={110}
                paddingAngle={4}
                label={({ percent }) => `${Math.round(percent)}%`}
                labelLine={false}
              >
                {pieSlices.map((entry: any, index: number) => (
                  <Cell key={`slice-${entry.scam_type}-${index}`} fill={entry.color} />
                ))}
              </Pie>
            </PieChart>
          </ResponsiveContainer>

          <table className="pie-type-table">
            <thead>
              <tr>
                <th>Hình thức</th>
                <th>%</th>
                <th>Mô tả</th>
              </tr>
            </thead>
            <tbody>
              {pieSlices.map((item: any) => {
                const isOther = item.scam_type === "other";
                const desc = isOther
                  ? others.map((s: any) => s.scam_type_label).join(", ")
                  : (scamTypeDesc[item.scam_type] ?? "");
                return (
                  <tr key={item.scam_type}>
                    <td>
                      <span className="pie-legend-swatch" style={{ backgroundColor: item.color }} />
                      {item.scam_type_label}
                    </td>
                    <td className="pie-type-pct">{item.percent}%</td>
                    <td className="pie-type-desc">{desc}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        <div className="panel chart-panel">
          <h2>Cảnh báo mỗi ngày (30 ngày)</h2>
          <div className="trend-summary-grid">
            <div>
              <span>Tổng cảnh báo 30 ngày</span>
              <strong>{trendTotal}</strong>
            </div>
            <div>
              <span>Ngày có nhiều cảnh báo nhất</span>
              <strong>{peakDay.reports > 0 ? `${peakDay.date_label}: ${peakDay.reports}` : "Chưa có"}</strong>
            </div>
          </div>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={trendData} margin={{ top: 12, right: 18, bottom: 8, left: 0 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="date_label" interval={4} tick={{ fontSize: 13 }} />
              <YAxis allowDecimals={false} tick={{ fontSize: 13 }} />
              <Tooltip formatter={(v: number) => [`${v} cảnh báo`, "Số cảnh báo"]} />
              <Bar dataKey="báo cáo lừa đảo" name="Số cảnh báo" fill="#2563eb" radius={[4, 4, 0, 0]} maxBarSize={28} />
            </BarChart>
          </ResponsiveContainer>
          <div className="trend-day-list">
            <strong>Các ngày có cảnh báo gần đây</strong>
            {activeTrendDays.length ? (
              <ul>
                {activeTrendDays.map((item) => (
                  <li key={item.date}>
                    <span>{item.date_label}</span>
                    <strong>{item.reports} cảnh báo</strong>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="muted">Chưa có cảnh báo trong 30 ngày gần đây.</p>
            )}
          </div>
        </div>
      </div>
      <div className="panel warning-guide">
        <div>
          <span className="eyebrow">Rút kinh nghiệm</span>
          <h2>Các kiểu lừa đảo thường gặp</h2>
          <p className="muted">Đọc các dấu hiệu dưới đây trước khi chuyển tiền, bấm vào link lạ, hoặc cung cấp mã OTP.</p>
        </div>
        <div className="warning-pattern-grid">
          {warningPatterns.map((pattern) => (
            <article className="warning-pattern-card" key={pattern.title}>
              <h3>{pattern.title}</h3>
              <div>
                <strong>Dấu hiệu dễ nhận ra</strong>
                <ul>
                  {pattern.signs.map((sign) => (
                    <li key={sign}>{sign}</li>
                  ))}
                </ul>
              </div>
              <p>
                <strong>Nên làm: </strong>
                {pattern.advice}
              </p>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}

function formatShortDate(date: string) {
  const [, month, day] = date.split("-");
  return `${day}/${month}`;
}
