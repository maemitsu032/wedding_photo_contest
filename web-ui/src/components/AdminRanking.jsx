import React, { useEffect, useState } from 'react';
import {
  Paper, Typography, Box, CircularProgress, Alert,
  Tabs, Tab, Table, TableHead, TableBody, TableRow, TableCell,
  Avatar, Tooltip
} from '@mui/material';
import { collection, getDocs } from 'firebase/firestore';
import { ref, getDownloadURL } from 'firebase/storage';
import { db, storage } from '../firebase';
import InfoIcon from '@mui/icons-material/Info';

const COLLECTION = 'contestScores';

export default function AdminRanking() {
  const [rows,    setRows]    = useState([]);
  const [targets, setTargets] = useState([]);
  const [selIdx,  setSelIdx]  = useState(0);
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState(null);

  /* -------- 全ドキュメント取得 -------- */
  useEffect(() => {
    (async () => {
      try {
        const snap     = await getDocs(collection(db, COLLECTION));
        const tasks    = [];
        const tSet     = new Set();

        snap.forEach(d => {
          const data = d.data();
          Object.keys(data.scores || {}).forEach(k => tSet.add(k));

          tasks.push(
            getDownloadURL(ref(storage, data.path))
              .catch(() => '')
              .then(url => ({ id: d.id, ...data, imgUrl: url }))
          );
        });

        setTargets(Array.from(tSet).sort());      // タブを名前順
        setRows(await Promise.all(tasks));
      } catch (e) {
        console.error(e);
        setError('データ取得に失敗しました');
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  /* -------- 並べ替え（選択タブのスコア降順） -------- */
  const sortedRows = () => {
    const key = targets[selIdx] ?? '';
    return [...rows].sort(
      (a, b) => (b.scores?.[key] ?? -Infinity) - (a.scores?.[key] ?? -Infinity)
    );
  };

  /* -------- UI -------- */
  if (loading) return <Center><CircularProgress/></Center>;
  if (error)   return <Center><Alert severity="error">{error}</Alert></Center>;

  return (
    <Paper sx={{ p: 3, overflowX: 'auto' }}>
      <Typography variant="h4" gutterBottom>
        管理者用ランキング
      </Typography>

      {/* ターゲット選択タブ */}
      {targets.length > 0 && (
        <Tabs
          value={selIdx}
          onChange={(_, v) => setSelIdx(v)}
          variant="scrollable"
          scrollButtons="auto"
          sx={{ mb: 2 }}
        >
          {targets.map(t => <Tab key={t} label={t} />)}
        </Tabs>
      )}

      {/* ランキング一覧 */}
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>順位</TableCell>
            <TableCell>写真</TableCell>
            <TableCell>名前</TableCell>
            <TableCell>顔数</TableCell>
            <TableCell align="right">
              スコア&nbsp;
              <Tooltip title="コサイン類似度平均">
                <InfoIcon fontSize="small" sx={{ verticalAlign:'middle' }} />
              </Tooltip>
            </TableCell>
          </TableRow>
        </TableHead>

        <TableBody>
          {sortedRows().map((r, idx) => (
            <TableRow key={r.id}>
              <TableCell>{idx + 1}</TableCell>
              <TableCell>
                <Avatar
                  src={r.imgUrl}
                  variant="rounded"
                  sx={{ width: 56, height: 56 }}
                />
              </TableCell>
              <TableCell>{r.userName}</TableCell>
              <TableCell>{r.faceCount}</TableCell>
              <TableCell align="right">
                {(r.scores?.[targets[selIdx]] ?? 0).toFixed(4)}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </Paper>
  );
}

/* 共通センタリング */
function Center({ children }) {
  return <Box sx={{ display:'flex', justifyContent:'center', my:4 }}>{children}</Box>;
}
