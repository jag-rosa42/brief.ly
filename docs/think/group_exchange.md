Morning Briefing

3 interservices connection:
Morning_Briefing <-> Content_Management
Morning_Briefing <-> AI_Processing
Morning_Briefing <-> Personalization

Content_Management

AI_Processing
- Endpoint sumarry of sumarry
- Topics Summary

Personalization





----------------------------------------------

Create one entry into the Morning briefing DB
/api/morning-briefing (post)
	-> /api/personalization/profiles (GET)
	-> /api/ai/cluster-topics ()





-----------------------------------------------
AI-Processing Services

- Create Summary
AI service launch /api/content/nromalized_articles (GET) => 50 articles
=> 50 summaries saved in the DB

- Create cluster topics?
	- ~~through embedding?~~
	- already done in COntent-management services by the NewsAPI categories
	- /api/content/articles (POST) body = { }





-------------
Morning-Briefing
-> /api/briefing/summary (GET)

	- Profile: Display_name, interest_list[4], avatar
	- Topics[7]: Science, Business, Entertainment, General, Health, Sport, Technologies
	- Articles relatied to topics clusters
	- Article summary
	- Topics Cluster Summary


	-> /api/content/articles (GET)
	-> /api/personalization/profiles (GET {user_id, display_name, focus_time})
	-> /api/ai/briefing-sumary (GET " sumarry of summary)

	=> Response
	{
		"profils"={
			"display_name": str,
			"interests": list[4],
			(account_id accessible through access_token),
			"avatar": (Image["jpeg"], Size = 3mo max),
			"articles_saved": [article_id,...article_n],
		},
		"topic_cluster_list": [
			"Topic_Cluster": {
				"topics_summary": Text,
				"name": str,
				"articles_list": [
					"article": {
						"source": str,
						"title": str,
						"summary": str,
						"article_id": UUID,
						"read_time": rand(0..5),
						"topic": str,
					},
					"article_n": {...}
				],
			},
		],
	}






Connection on Dashboard
	-> launch an request /api/briefing/summary (GET)




dashboard/articles/article-id

-> get /api/content/article_id
{
	article_content:,
	users_list: [user123, user456]
}
