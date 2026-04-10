import styles from "./FeedbackSection.module.css";

function FeedbackSection({ ui, feedback }) {
  return (
    <div className={styles.feedbackTabLayout}>
      <div className={ui.card}>
        <h3>Average Rating</h3>
        <p className={ui.metric}>{feedback?.average_rating || 0} / 5</p>
      </div>
      <div className={ui.card}>
        <h3>Total Feedback</h3>
        <p className={ui.metric}>{feedback?.total_feedback_count || 0}</p>
      </div>
      <div className={`${ui.cardLarge} ${styles.feedbackNarrow}`}>
        <h3>Rating Distribution</h3>
        <div className={ui.listWrap}>
          {[5, 4, 3, 2, 1].map((r) => (
            <div key={r} className={ui.feedbackRowPlain}>
              <span>{r} star</span>
              <strong>{feedback?.[`rating_${r}`] || 0}</strong>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default FeedbackSection;
