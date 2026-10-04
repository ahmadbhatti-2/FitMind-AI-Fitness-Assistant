const EXERCISE_IMAGES = [
  { match: /bench press|dumbbell press|chest press|push-up|push up|chest fly|cable crossover|chest/i, image: 'photo-1534367610401-9f5ed68180aa' },
  { match: /row|pull-up|pull up|lat pulldown|face pull|back extension|back/i, image: 'photo-1583454110551-21f2fa2afe61' },
  { match: /squat|lunge|leg press|leg curl|leg extension|glute|calf raise|deadlift|step-up|lower body|legs/i, image: 'photo-1579758629938-03607ccdbaba' },
  { match: /run|cycling|jump rope|burpee|mountain climber|high knees|cardio|walk|stair climber|battle rope|sled push|sled pull/i, image: 'photo-1538805060514-97d9cc17730c' },
  { match: /shoulder press|lateral raise|front raise|bicep curl|tricep|arm|farmer carry|wrist curl/i, image: 'photo-1583454110551-21f2fa2afe61' },
];

const MEAL_IMAGES_BY_ID = {
  mt_001: 'photo-1490645935967-10de6ba17061',
  mt_002: 'photo-1488477181946-6428a0291777',
  mt_003: 'photo-1512621776951-a57141f2eefd',
  mt_004: 'photo-1546069901-ba9599a7e63c',
  mt_005: 'photo-1547592180-85f173990554',
  mt_006: 'photo-1467003909585-2f8a72700288',
  mt_007: 'photo-1547592180-85f173990554',
  mt_008: 'photo-1467003909585-2f8a72700288',
  mt_009: 'photo-1546069901-ba9599a7e63c',
  mt_010: 'photo-1547592180-85f173990554',
  mt_011: 'photo-1512621776951-a57141f2eefd',
  mt_012: 'photo-1490645935967-10de6ba17061',
  mt_013: 'photo-1571771894821-ce9b6c11b08e',
  mt_014: 'photo-1488477181946-6428a0291777',
  mt_015: 'photo-1540420773420-3366772f4999',
  mt_016: 'photo-1488477181946-6428a0291777',
  mt_017: 'photo-1571771894821-ce9b6c11b08e',
  mt_018: 'photo-1512621776951-a57141f2eefd',
  mt_019: 'photo-1546069901-ba9599a7e63c',
  mt_020: 'photo-1547592180-85f173990554',
  mt_021: 'photo-1490645935967-10de6ba17061',
  mt_022: 'photo-1490645935967-10de6ba17061',
  mt_023: 'photo-1488477181946-6428a0291777',
  mt_024: 'photo-1540420773420-3366772f4999',
  mt_025: 'photo-1547592180-85f173990554',
  mt_026: 'photo-1546069901-ba9599a7e63c',
  mt_027: 'photo-1467003909585-2f8a72700288',
  mt_028: 'photo-1467003909585-2f8a72700288',
  mt_029: 'photo-1547592180-85f173990554',
  mt_030: 'photo-1512621776951-a57141f2eefd',
  mt_031: 'photo-1488477181946-6428a0291777',
  mt_032: 'photo-1490645935967-10de6ba17061',
  mt_033: 'photo-1547592180-85f173990554',
  mt_034: 'photo-1546069901-ba9599a7e63c',
  mt_035: 'photo-1467003909585-2f8a72700288',
};

const MEAL_IMAGES = [
  { match: /chicken|turkey|beef/i, image: 'photo-1546069901-ba9599a7e63c' },
  { match: /salmon|tuna|fish|shrimp|sardine/i, image: 'photo-1467003909585-2f8a72700288' },
  { match: /tofu|tempeh|edamame/i, image: 'photo-1512621776951-a57141f2eefd' },
  { match: /lentil|roti|paneer|chickpea|quinoa|bean/i, image: 'photo-1547592180-85f173990554' },
  { match: /oat|egg|dalia|toast/i, image: 'photo-1490645935967-10de6ba17061' },
  { match: /yogurt|berries|dates|chia|fruit/i, image: 'photo-1488477181946-6428a0291777' },
  { match: /banana|shake|smoothie|milk|peanut/i, image: 'photo-1571771894821-ce9b6c11b08e' },
  { match: /hummus|veggie|salad|vegetable|greens/i, image: 'photo-1540420773420-3366772f4999' },
];

function unsplashImage(id, width = 900) {
  return `https://images.unsplash.com/${id}?auto=format&fit=crop&w=${width}&q=85`;
}

export function exerciseImage(name = '') {
  const match = EXERCISE_IMAGES.find(({ match: pattern }) => pattern.test(name));
  return match ? unsplashImage(match.image) : null;
}

export function workoutImage(workout) {
  const firstExercise = workout?.exercises?.find((exercise) => exerciseImage(exercise.name));
  return exerciseImage(firstExercise?.name || workout?.title || '');
}

export function mealImage(meal) {
  const catalogImage = MEAL_IMAGES_BY_ID[meal?.id];
  if (catalogImage) return unsplashImage(catalogImage);

  const description = `${meal?.meal_name || ''} ${(meal?.ingredients || []).join(' ')}`.replaceAll('_', ' ');
  const match = MEAL_IMAGES.find(({ match: pattern }) => pattern.test(description));
  return match ? unsplashImage(match.image) : null;
}
