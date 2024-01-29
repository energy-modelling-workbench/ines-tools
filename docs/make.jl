using Documenter

pages=[
    "Home" => "index.md",
    "Third Party Tools" => Any[
        "CorRES" => joinpath("third_party_tools", "CorRES.md"),
        "AIDRES" => joinpath("third_party_tools", "AIDRES.md"),
        "ChaProEV" => joinpath("third_party_tools", "ChaProEV.md")
    ],
    "Examples" => Any[
        "Stepstone exercise" => joinpath("examples", "stepstone_exercise.md"),
        #"Workflow 20230815" => joinpath("examples", "workflow_20230815.md")
    ]
]

makedocs(
    sitename="ines-data-tools",
    format=Documenter.HTML(prettyurls=get(ENV, "CI", nothing) == "true"),
    pages=pages,
)

deploydocs(repo="github.com/energy-modelling-workbench/ines-data-tools.git", versions=["stable" => "v^", "v#.#"])