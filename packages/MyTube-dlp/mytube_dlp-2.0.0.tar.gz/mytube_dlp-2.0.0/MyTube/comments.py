import os
import json
import subprocess
from .utils import Channel
from .utils import get_cookie_file

class CommentsManager:
	def __init__(self, link, count, cookies=None, yt_dlp="yt-dlp"):
		self.link = link
		self.count = count
		self.cookies = cookies
		self.yt_dlp = yt_dlp
		self.data = []
	def __str__(self): return f"Comments({self.count})"
	def __len__(self): return self.count
	def get(self) -> list:
		if not self.data:
			cookie_file = get_cookie_file(self.cookies) if self.cookies else None
			cmd = [
				self.yt_dlp,
				"--quiet",
				"--no-playlist",
				"--no-warnings",
				"--get-comments",
				"--skip-download",
				*(["--cookies", cookie_file] if cookie_file else []),
				"--dump-single-json",
				self.link
			]
			result = subprocess.run(cmd, capture_output=True, text=True)
			_vid_info = json.loads(result.stdout)
			self.data = _vid_info.get("comments")

			if cookie_file and os.path.exists(cookie_file): os.remove(cookie_file)
		return list(map(lambda x: Comment(x, video_url=self.link), self.data))

class Comment:
	def __init__(self, args, video_url):
		self.args = args
		self.id = args.get("id")
		self.url = f"{video_url}&lc={args.get('id')}"
		self.text = str(args.get("text", ""))
		self.likes = int(args.get("like_count", 0))
		self.is_pinned = args.get("is_pinned", False)
		self._parent = "root" if args.get("parent") == "root" else f"{video_url}&lc={args.get('parent')}"
	
	def __str__(self): return self.text
	def __repr__(self): return f"Comment({self.id})"
	@property
	def author(self) -> Channel:
		id = self.args.get("author_id")
		url = self.args.get("author_url")
		name = self.args.get("author")
		return Channel(id=id, url=url, name=name)
