from DirectLine import DirectLineEngine

de = DirectLineEngine('https://default26fec82afef145d99d67a5616783d7.46.environment.api.powerplatform.com/powervirtualagents/botsbyschema/crdc1_mwsFirstCopilot/directline/token?api-version=2022-03-01-preview')

# token, conversationId = de.get_token()
# print(token)
# print(conversationId)

token = "eyJhbGciOiJSUzI1NiIsImtpZCI6IjVnZEdBYmd1OExXWGZCOXZFZFY3ZUVveGE1cyIsIng1dCI6IjVnZEdBYmd1OExXWGZCOXZFZFY3ZUVveGE1cyIsInR5cCI6IkpXVCJ9.eyJib3QiOiIwMTdhM2UwOS1mZmQ4LTQzYzYtODFhMC0xN2ViNWM5ZDAyYjIiLCJzaXRlIjoieHdBTnJxSVJUcTgiLCJjb252IjoiRWZ5VFpPZWJYSzY3WU1PVnpHM3ZRMC11cyIsInVzZXIiOiI3ZjFiNjZhMC05NWViLTQ3ZGItOTQzNS01M2Y0ODFjNDVjNGMiLCJuYmYiOjE3MDYwNjY5MTcsImV4cCI6MTcwNjA3MDUxNywiaXNzIjoiaHR0cHM6Ly9kaXJlY3RsaW5lLmJvdGZyYW1ld29yay5jb20vIiwiYXVkIjoiaHR0cHM6Ly9kaXJlY3RsaW5lLmJvdGZyYW1ld29yay5jb20vIn0.lCzcLFnJiM6wks6dOsxvEB6z7ZjlknYsGcwRoU0dJhyyDX-YNj4-5TpTt8sDmlVdYDi12-5i8BDm5CK1pMlfWObdRuS4fCnVAG9C0l-k1T6Cuf2BVfnzmVJMxNdrJEWLVbhyXYOMq7OVNebZ-IR60O4SHxWGxIQMwarAYBXJk1pPupxsu4jvM17pWJvPs_RO-vBZnLi-lfBJsX8BrPHmyHWIIJn4JDHzl_CGifr3E1ClkOAja7PS_CVJmaKuqMSDrBlGWq6bdxFAz3B-mZ8AwF2C8LSlviwHmv6Q1T9myqLzsw7Oagxd2aY4Cj5g8F4oDBph68rP0_g2S97RuZPEKA"
conversationId = "EfyTZOebXK67YMOVzG3vQ0-us"

# conv = de.create_conversation(token)
# print(conv)

# r = de.refresh_token(token)
# print(r)
r = de.send_activity(token, conversationId, "My name is James.")
print(r)
activity = de.get_activity(token, conversationId)
print(activity["activities"][-1]["text"])




