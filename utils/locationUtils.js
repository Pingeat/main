const { getDistance } = require('geolib');
const branches = require('../data/branches.json');

const DEFAULT_RADIUS_KM = Number(process.env.BRANCH_RADIUS_KM || 3);

function findClosestBranch(latitude, longitude, radiusKm = DEFAULT_RADIUS_KM) {
  let closest = null;
  let minDistance = Infinity;
  for (const [name, info] of Object.entries(branches)) {
    const [branchLat, branchLon] = info.coordinates;
    const distance = getDistance(
      { latitude, longitude },
      { latitude: branchLat, longitude: branchLon }
    );
    if (distance < minDistance) {
      minDistance = distance;
      closest = { name, map_link: info.map_link, contact: info.contact, distance };
    }
  }
  if (closest && minDistance <= radiusKm * 1000) {
    return closest;
  }
  return null;
}

module.exports = { findClosestBranch };
