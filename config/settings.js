module.exports = {
  ADMIN_NUMBERS: (process.env.ADMIN_NUMBERS || '').split(',').filter(Boolean),
  ORDERS_CSV: process.env.ORDERS_CSV || 'orders.csv',
  USER_LOG_CSV: process.env.USER_LOG_CSV || 'user_activity_log.csv',
  PROMO_LOG_CSV: process.env.PROMO_LOG_CSV || 'promo_sent_log.csv',
  FEEDBACK_CSV: process.env.FEEDBACK_CSV || 'feedback.csv',
  OPEN_TIME: parseInt(process.env.OPEN_TIME || '9', 10),
  CLOSE_TIME: parseInt(process.env.CLOSE_TIME || '23', 10),
  OFF_HOUR_USERS_CSV: process.env.OFF_HOUR_USERS_CSV || 'offhour_users.csv',
  BRANCH_STATUS: {
    kondapur: true,
    madhapur: true,
    manikonda: true,
    nizampet: true,
    nanakramguda: true
  },
  BRANCH_DISCOUNTS: {
    kondapur: 0,
    madhapur: 0,
    manikonda: 0,
    nizampet: 0,
    nanakramguda: 0
  },
  BRANCH_BLOCKED_USERS: {
    kondapur: new Set(),
    madhapur: new Set(),
    manikonda: new Set(),
    nizampet: new Set(),
    nanakramguda: new Set()
  }
};
