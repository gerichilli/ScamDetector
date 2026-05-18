import { useQuery } from "@tanstack/react-query";
import { CartesianGrid, Cell, Legend, Line, LineChart, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api } from "../api/client";

const scamTypeLabels: Record<string, string> = {
  bank_transfer: "Chuyển khoản nhận tiền rồi biến mất",
  fake_seller: "Bán hàng giả hoặc không giao hàng",
  fake_job: "Việc làm giả, bắt đóng phí trước",
  investment: "Đầu tư lợi nhuận cao bất thường",
  impersonation: "Giả danh người quen hoặc cơ quan",
  call_low: "Cuộc gọi rủi ro thấp",
  call_medium: "Cuộc gọi đáng nghi",
  call_high: "Cuộc gọi rủi ro cao",
  call_critical: "Cuộc gọi rất nguy hiểm",
  "Thong bao trung thuong yeu cau dong phi": "Thông báo trúng thưởng, yêu cầu đóng phí",
  "Gia danh ngan hang xin ma OTP": "Giả danh ngân hàng xin mã OTP",
  "Gia danh cong an doa lien quan vu an": "Giả danh công an, dọa liên quan vụ án",
  "Moi dau tu loi cao": "Mời đầu tư lợi nhuận cao",
  other: "Hình thức khác",
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

  // Simplify pie: show top N slices and group the rest into "Khác"
  const TOP_N = 5;
  const sorted = [...byTypeWithPercent].sort((a, b) => (b.count ?? 0) - (a.count ?? 0));
  const top = sorted.slice(0, TOP_N);
  const others = sorted.slice(TOP_N);
  const othersCount = others.reduce((s, it) => s + (it.count ?? 0), 0);
  const pieSlices = [...top];
  if (othersCount > 0) {
    pieSlices.push({
      scam_type: "other",
      scam_type_label: scamTypeLabels["other"],
      count: othersCount,
      color: getPieColor("other", TOP_N),
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

          <div className="panel pie-legend-table">
            <strong>Ghi chú</strong>
            <div className="pie-legend-grid">
              {pieSlices.map((item: any) => (
                <div className="pie-legend-row" key={item.scam_type}>
                  <span className="pie-legend-swatch" style={{ backgroundColor: item.color }} />
                  <span className="pie-legend-label">{item.scam_type_label}</span>
                  <strong>{item.percent}%</strong>
                </div>
              ))}
            </div>
          </div>
        </div>
        <div className="panel chart-panel">
          <h2>Xu hướng 30 ngày</h2>
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
            <LineChart data={trendData} margin={{ top: 12, right: 18, bottom: 8, left: 0 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date_label" interval={4} />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="báo cáo lừa đảo" stroke="#dc2626" strokeWidth={3} dot={{ r: 4 }} activeDot={{ r: 7 }} />
              <Line type="monotone" dataKey="đối tượng mới" stroke="#059669" strokeWidth={3} dot={{ r: 4 }} activeDot={{ r: 7 }} />
            </LineChart>
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
