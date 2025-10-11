#!/bin/bash
# Emoji Removal Script
# Removes all emojis from the entire codebase

echo "=== EMOJI REMOVAL TOOL ==="
echo ""
echo "This script will remove all emojis from:"
echo "  - README.md and documentation"
echo "  - Kubernetes YAML files"
echo "  - Shell scripts"
echo "  - Python files"
echo "  - Terraform files"
echo ""

read -p "Continue? (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled"
    exit 0
fi

echo ""
echo "Removing emojis from README.md..."
sed -i 's/📁 //g; s/🚀 //g; s/📊 //g; s/🛡️ //g; s/📚 //g; s/🔍 //g; s/🎯 //g; s/🔧 //g; s/📝 //g; s/✨ //g; s/🎉 //g; s/🏗️ //g; s/🏆 //g; s/✅ //g; s/❌ //g; s/⚠️ //g; s/🔐 //g; s/🔄 //g; s/📈 //g; s/📋 //g; s/🆘 //g; s/📄 //g; s/🤝 //g' README.md

echo "Removing emojis from Kubernetes files..."
find k8s -name "*.yaml" -type f -exec sed -i 's/🚀//g; s/📁//g; s/✅//g; s/❌//g; s/⚠️//g; s/🔄//g; s/⏳//g; s/🧪//g; s/🎉//g' {} \;

echo "Removing emojis from shell scripts..."
find scripts -name "*.sh" -type f -exec sed -i 's/✅//g; s/❌//g; s/⚠️//g; s/🚀//g; s/📁//g; s/🔍//g; s/💰//g; s/⏰//g; s/🔒//g; s/📊//g; s/🎯//g; s/🔧//g' {} \;

echo "Removing emojis from Python files..."
find . -name "*.py" -type f -exec sed -i 's/✅//g; s/❌//g; s/📚//g; s/🔍//g' {} \;

echo "Removing emojis from Terraform files..."
find terraform -name "*.tf" -type f -exec sed -i 's/👈//g; s/✅//g; s/❌//g' {} \;

echo ""
echo "Done! All emojis removed from codebase"
echo ""
echo "Run 'git diff' to see what changed"


