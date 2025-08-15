module.exports = {
  ADMIN_NUMBERS: (process.env.ADMIN_NUMBERS || '').split(',').filter(Boolean),
  ORDERS_CSV: process.env.ORDERS_CSV || 'orders.csv'
};
