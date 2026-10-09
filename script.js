import http from 'k6/http';
import { check } from 'k6';

export const options = {
  vus: 100,
  duration: '30s',
};

export default function () {
  const res = http.get('http://host.docker.internal:5000/transactions/search');

  if (res.status !== 200) {
    console.log(`ERROR status=${res.status}`);
  }

  check(res, {
    'status is 200': (r) => r.status === 200,
  });
}
