module.exports = {
  ADMIN_NUMBERS: (process.env.ADMIN_NUMBERS || '').split(',').filter(Boolean),
  ORDERS_CSV: process.env.ORDERS_CSV || 'orders.csv',
  FEEDBACK_CSV: process.env.FEEDBACK_CSV || 'feedback.csv',
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
